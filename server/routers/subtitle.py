from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
from publish_pipeline import publish_pipeline, PlayRequest

router = APIRouter()

manager = WebSocketManager()
# send subtitle after TTS ends instead of at play start because sleep() blocks the thread, and blocking should be minimized in play stage.
async def on_play_start(inp: PlayRequest):
    await manager.broadcast(inp.text)
publish_pipeline.event_manager.subscribe('play_stage:start', on_play_start)

@router.websocket('/subtitle')
async def subtitle(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)