from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
from publish_pipeline import publish_pipeline, PlayRequest
import asyncio

SUBTITLE_DELAY = 3

router = APIRouter()

manager = WebSocketManager()
# send subtitle after TTS ends instead of at play start because sleep() blocks the thread, and blocking should be minimized in play stage.
async def on_tts_end(inp, out: PlayRequest):
    await asyncio.sleep(SUBTITLE_DELAY)
    await manager.broadcast(out.text)
publish_pipeline.event_manager.subscribe('tts_stage:end', on_tts_end)

@router.websocket('/subtitle')
async def subtitle(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)