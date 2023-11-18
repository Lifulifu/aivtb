from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import yaml
from typing import Callable, AsyncGenerator
import asyncio
import json
import pytchat
from main import construct_message
from llm import get_llm_text_stream, to_chunks

# load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

class AsyncWorker():
    def __init__(self, process_task: Callable, in_queue = None, cooldown = 0):
        # submit() a task and it will be queued in in_queue.
        # The run() loop receives a task from in_queue, and process it with process_task(),
        # then the next task can be processed.
        self.process_task = process_task
        self.in_queue = asyncio.Queue() if in_queue is None else in_queue
        self.cooldown = cooldown

    async def run(self):
        while True:
            task = await self.in_queue.get()
            await self.process_task(task)
            self.in_queue.task_done()

            if self.cooldown > 0: await asyncio.sleep(self.cooldown)

    def start(self):
        self.worker = asyncio.create_task(self.run())

    async def submit(self, message: str):
        await self.in_queue.put(message)

    async def end(self):
        if self.worker: self.worker.cancel()
        await asyncio.gather(self.worker, return_exceptions=True)

response_queue = asyncio.Queue()
async def gen_response_text_stream(message: str):
    text_stream = get_llm_text_stream(construct_message(message, prompt=config['prompt']))
    accum = ''
    async for piece in text_stream:
        accum += piece
        await response_queue.put({'q': message, 'a': accum})
infer_worker = AsyncWorker(gen_response_text_stream, cooldown=2)
infer_worker.start()


# start server
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/chat')
async def chat(message: str):
    # Submit message
    print('\nQ:', message)
    await infer_worker.submit(message)

# Catches cancel signal from client
async def async_stream_wrapper(gen):
    try:
        async for item in gen:
            yield item
    except asyncio.CancelledError:
        print("stream client cancelled")

def to_sse_string(data: dict):
    return f'data: {json.dumps(data)}\n\n'

@app.get('/stream_response')
async def stream_response(request: Request):
    async def gen():
        while True:
            piece = await response_queue.get()
            yield to_sse_string(piece)

    return StreamingResponse(async_stream_wrapper(gen()), media_type='text/event-stream')

@app.get('/stream_yt_comments')
async def stream_yt_comments(video_id: str, request: Request):
    chat = pytchat.create(video_id=video_id)
    async def gen():
        while chat.is_alive():
            async for item in chat.get().async_items():
                chunk = {
                    'time': item.datetime,
                    'name': item.author.name,
                    'message': item.message
                }
                yield to_sse_string(chunk)

    return StreamingResponse(gen(), media_type='text/event-stream')