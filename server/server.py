from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from wsmanager import WebSocketManager
import config
import asyncio
import pytchat
from worker import AsyncSequentialWorker, AsyncPipelineWorker
from pydantic import BaseModel
from azure.cognitiveservices.speech import AudioDataStream
from contextlib import asynccontextmanager
from typing import List

from llm import get_llm_text_stream, to_chunks, construct_message, add_punctuation, remove_prefix, have_prefix
from tts import get_openai_tts_audio, play_openai_speech, get_azure_tts_audio, play_azure_speech

class UserMessageRequest(BaseModel):
    messages: List[dict[str, str]]
    temperature: float

# Functionality for the 'publish_ai_response' and 'stream_subtitle' endpoints
subtitle_queue = asyncio.Queue()

async def tts_stage(req):
    audio = await get_azure_tts_audio(req['processed'])
    return { **req, 'audio': audio }

async def play_stage(req):
    await play_azure_speech(req['audio'], req['device'])
    await subtitle_queue.put(req['original']) # will be sent to subtitle_queue

publish_worker = AsyncPipelineWorker([tts_stage, play_stage], debug=True, process_task_names=['tts', 'play'])
publish_worker.start()

# Functionality for the 'send_user_message' and 'stream_ai_response' endpoints
ai_response_queue = asyncio.Queue()

async def collect_ai_response(req: UserMessageRequest):
    text_stream = get_llm_text_stream(
        construct_message(req.messages, prompt=config.prompt),
        temperature=req.temperature)
    accum = ''
    async for piece in text_stream:
        accum += piece
        await ai_response_queue.put([ *req.messages, {"role": "assistant", "content": accum} ])

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

# get/post endpoints
@app.post('/send_user_message')
async def chat(req: UserMessageRequest):
    # Submit message
    print('\nQ:', req.messages)
    await infer_worker.submit(req)

class AiResponse(BaseModel):
    q: str
    a: str
    device: int = -1

@app.post('/publish_ai_response')
async def publish_ai_response(response: AiResponse):
    original = []
    processed = []
    print('publish', response)

    # speak question only if it is player message
    if not have_prefix(response.q):
        chunks = to_chunks(remove_prefix(response.q), min_len=20)
        original.extend(chunks)
        processed.extend(
            list(map(lambda chunk: add_punctuation(chunk), chunks)))

    chunks = to_chunks(response.a, min_len=20)
    original.extend(chunks)
    processed.extend(
        list(map(lambda chunk: add_punctuation(chunk), chunks)))

    for ori_chunk, proc_chunk in zip(original, processed):
        await publish_worker.submit({ 'original': ori_chunk, 'processed': proc_chunk, 'device': response.device })

# websocket endpoints
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

subtitle_manager = WebSocketManager()
@app.websocket('/stream_subtitle')
async def stream_subtitle(websocket: WebSocket):
    await subtitle_manager.connect(websocket)

    async def task():
        result = await subtitle_queue.get()
        print('broadcast:', result)
        await subtitle_manager.broadcast(result)

    await subtitle_manager.run_async_worker(websocket, task=task)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print('server shutdown')
    await infer_worker.end()
    await publish_worker.end()