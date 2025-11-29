from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, space_id: int):
        await websocket.accept()
        if space_id not in self.active_connections:
            self.active_connections[space_id] = []
        self.active_connections[space_id].append(websocket)

    def disconnect(self, websocket: WebSocket, space_id: int):
        if space_id in self.active_connections:
            self.active_connections[space_id].remove(websocket)

    async def broadcast(self, message: str, space_id: int):
        if space_id in self.active_connections:
            for connection in self.active_connections[space_id]:
                await connection.send_text(message)

manager = ConnectionManager()
