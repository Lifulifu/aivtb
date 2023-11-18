from fastapi import WebSocket, WebSocketDisconnect
from typing import Callable
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print('connected', len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, data: object):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def run_async_worker(self, websocket: WebSocket, task: Callable):
        # task is expected to be a function that returns bool that tells wether to abort (no return value or False means continue)
        async def check_client_status():
            try:
                await websocket.receive_text()
                return False
            except WebSocketDisconnect:
                return True

        while True:
            # Do task or receive client cancel signal.
            # Note that this line doesn't work in python3.11, it's a bug of that version. Currently using 3.10
            done, pending = await asyncio.wait([task(), check_client_status()], return_when=asyncio.FIRST_COMPLETED)
            # Cancel all other tasks
            while len(pending) > 0: pending.pop().cancel()
            abort = done.pop().result()
            if abort:
                self.disconnect(websocket)
                print('disconnected', len(self.active_connections))
                break