from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
from publish_pipeline import publish_pipeline, PlayRequest

router = APIRouter()

manager = WebSocketManager()


async def on_play_start(inp: PlayRequest):
    await manager.broadcast(
        {
            "status": "start",
            "role": inp.role,
            "text": inp.text,
            "remain": publish_pipeline.workers[-1].in_queue.qsize(),
        }
    )


publish_pipeline.event_manager.subscribe("play_stage:start", on_play_start)


async def on_play_end(inp: PlayRequest, out: str):
    await manager.broadcast(
        {
            "status": "end",
            "role": inp.role,
            "text": inp.text,
            "remain": publish_pipeline.workers[-1].in_queue.qsize(),
        }
    )


publish_pipeline.event_manager.subscribe("play_stage:end", on_play_end)


@router.websocket("/subtitle")
async def subtitle(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
