
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
import pytchat

router = APIRouter()

manager = WebSocketManager()

@router.websocket('/yt_comments/{video_id}')
async def yt_comments(websocket: WebSocket, video_id: str):
    await manager.connect(websocket)

    chat = pytchat.create(video_id=video_id)
    try:
        while True:
            if chat.is_alive():
                async for item in chat.get().async_items():
                    chunk = {
                        'time': item.datetime,
                        'name': item.author.name,
                        'message': item.message
                    }
                    await manager.broadcast(chunk)
            else:
                return True # abort
    except WebSocketDisconnect:
        manager.disconnect(websocket)