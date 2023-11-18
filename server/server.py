from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from wsmanager import WebSocketManager
import yaml
import asyncio
import json
import pytchat
from main import construct_message
from llm import get_llm_text_stream, ChunkCollector
from worker import AsyncSequentialWorker, AsyncPipelineWorker

# load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

def logger(chunk):
    print('fetch:', chunk)
    return chunk

async def mock_tts(chunk):
    await asyncio.sleep(2)
    print(f'say: {chunk}')
    return chunk

ai_response_queue = asyncio.Queue()
finished_tts_queue = asyncio.Queue()
# chunk -> (in_queue) -> speech buffer -> play speech -> (out_queue) -> chunk
pipeline = AsyncPipelineWorker(stages=[logger, mock_tts], out_queue=finished_tts_queue)
pipeline.start()

async def run_infer_task(message: str):
    text_stream = get_llm_text_stream(construct_message(message, prompt=config['prompt']))

    chunk_coll = ChunkCollector(min_len=30)
    accum = ''
    async for piece in text_stream:
        # send to ai_response_queue when text is generated
        accum += piece
        await ai_response_queue.put({'q': message, 'a': accum})

        # send to finished_tts_queue when tts chunk is finished
        chunk = chunk_coll.collect(piece)
        if chunk:
            await pipeline.submit({
                'q': message,
                'a': accum,
                'chunk': chunk
            })

    if chunk_coll.remain_chunk():
        await pipeline.submit({
            'q': message,
            'a': accum,
            'chunk': chunk_coll.chunk
        })

infer_worker = AsyncSequentialWorker(run_infer_task, cooldown=2)
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

# @app.post('/commit_response')
# async def 

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

finished_tts_manager = WebSocketManager()
@app.websocket('/stream_finished_tts')
async def stream_finished_tts(websocket: WebSocket):
    await finished_tts_manager.connect(websocket)

    async def task():
        result = await finished_tts_queue.get()
        await finished_tts_manager.broadcast(result)

    await finished_tts_manager.run_async_worker(websocket, task=task)
