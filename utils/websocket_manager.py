from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Format: {"role_user_id": [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: int, role: str, websocket: WebSocket):
        await websocket.accept()
        key = f"{role}_{user_id}"
        if key not in self.active_connections:
            self.active_connections[key] = []
        self.active_connections[key].append(websocket)

    def disconnect(self, user_id: int, role: str, websocket: WebSocket):
        key = f"{role}_{user_id}"
        if key in self.active_connections:
            if websocket in self.active_connections[key]:
                self.active_connections[key].remove(websocket)
            if len(self.active_connections[key]) == 0:
                del self.active_connections[key]

    async def send_to_user(self, user_id: int, role: str, data: dict):
        key = f"{role}_{user_id}"
        if key in self.active_connections:
            dead_sockets = []
            for ws in self.active_connections[key]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_sockets.append(ws)
            
            for ws in dead_sockets:
                self.disconnect(user_id, role, ws)

manager = ConnectionManager()
