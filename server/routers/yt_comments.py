
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
from wsmanager import WebSocketManager
import pytchat

router = APIRouter()

manager = WebSocketManager()

# Can't make it a worker because pytchat only works on the main thread
@router.websocket('/yt_comments/{video_id}')
async def yt_comments(websocket: WebSocket, video_id: str):
    await manager.connect(websocket)

    chat = pytchat.create(video_id=video_id)
    try:
        while True:
            # client must ping the server to keep the connection alive
            await websocket.receive_text()
            if chat.is_alive():
                async for item in chat.get().async_items():
                    chunk = {
                        'time': item.datetime,
                        'name': item.author.name,
                        'message': item.message
                    }
                    await manager.broadcast(chunk)
            else:
                manager.disconnect(websocket)
                return True # abort
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except WebSocketException:
        manager.disconnect(websocket)