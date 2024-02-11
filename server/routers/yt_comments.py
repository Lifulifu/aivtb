from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from wsmanager import WebSocketManager
from utils.yt_livechat import YTLiveChat

router = APIRouter()
manager = WebSocketManager()
live_chat = YTLiveChat("client_secret.json")


@router.websocket("/yt_live_chat/{live_chat_id}")
async def yt_live_chat(websocket: WebSocket, live_chat_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            messages = live_chat.get_unread_live_chat_messages(live_chat_id)
            await manager.broadcast(messages)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/yt_live_streams")
def yt_live_streams():
    return live_chat.get_live_streams()
