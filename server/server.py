from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from wsmanager import WebSocketManager
import yaml
import asyncio
import pytchat
from main import construct_message
from llm import get_llm_text_stream, to_chunks
from worker import AsyncSequentialWorker, AsyncPipelineWorker
from pydantic import BaseModel


# load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# setup workers
async def stage1(chunk):
    print('stage1:', chunk)
    return chunk

async def stage2(chunk):
    await asyncio.sleep(2)
    print('stage2', chunk)
    return chunk

pipeline = AsyncPipelineWorker([stage1, stage2])
pipeline.start()

ai_response_queue = asyncio.Queue()
async def collect_ai_response(message: str):
    text_stream = get_llm_text_stream(construct_message(message, prompt=config['prompt']))
    accum = ''
    async for piece in text_stream:
        # send to ai_response_queue when text is generated
        accum += piece
        await ai_response_queue.put({'q': message, 'a': accum})

infer_worker = AsyncSequentialWorker(collect_ai_response, cooldown=2)
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

class AiResponse(BaseModel):
    q: str
    a: str

@app.post('/publish_ai_response')
async def publish_ai_response(response: AiResponse):
    chunks = to_chunks(response.a, min_len = 30)
    for chunk in chunks:
        await pipeline.submit(chunk)

# Catches cancel signal from client
async def async_stream_wrapper(gen):
    try:
        async for item in gen:
            yield item
    except asyncio.CancelledError:
        print("stream client cancelled")

yt_comments_manager = WebSocketManager()
@app.websocket('/stream_yt_comments/{video_id}')
async def stream_yt_comments(websocket: WebSocket, video_id: str):
    await yt_comments_manager.connect(websocket)

    chat = pytchat.create(video_id=video_id)
    async def task():
        if chat.is_alive():
            async for item in chat.get().async_items():
                chunk = {
                    'time': item.datetime,
                    'name': item.author.name,
                    'message': item.message
                }
                await yt_comments_manager.broadcast(chunk)
        else:
            return True # abort

    await yt_comments_manager.run_async_worker(websocket, task=task)

ai_response_manager = WebSocketManager()
@app.websocket('/stream_ai_response')
async def stream_ai_response(websocket: WebSocket):
    await ai_response_manager.connect(websocket)

    async def task():
        result = await ai_response_queue.get()
        await ai_response_manager.broadcast(result)

    await ai_response_manager.run_async_worker(websocket, task=task)

# finished_tts_manager = WebSocketManager()
# @app.websocket('/stream_finished_tts')
# async def stream_finished_tts(websocket: WebSocket):
#     await finished_tts_manager.connect(websocket)

#     async def task():
#         result = await finished_tts_queue.get()
#         await finished_tts_manager.broadcast(result)

#     await finished_tts_manager.run_async_worker(websocket, task=task)
