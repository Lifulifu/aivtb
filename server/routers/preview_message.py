from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
from textgen_pipeline import textgen_pipeline

router = APIRouter()

manager = WebSocketManager()


async def on_textgen_end(inp, message):
    await manager.broadcast(message)


textgen_pipeline.event_manager.subscribe("textgen_stage:end", on_textgen_end)


@router.websocket_route("/preview_message")
async def preview_message(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
