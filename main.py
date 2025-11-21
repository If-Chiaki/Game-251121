from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import uuid
from typing import List
from game_core import game

app = FastAPI()

# 挂载静态文件，用于访问 index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return FileResponse('static/index.html')

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        # 发送初始状态
        await websocket.send_json({"type": "state", "data": game.get_snapshot()})
        
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            payload = data.get("payload", {})
            
            response = {"success": False, "message": "Unknown action"}
            
            if action == "join":
                name = payload.get("name", "Unknown")
                success, msg = game.add_player(name, client_id)
                response = {"success": success, "message": msg}
                
            elif action == "start_game":
                success, msg = game.start_game()
                response = {"success": success, "message": msg}
                
            elif action == "roll":
                success, msg = game.roll_dice(client_id)
                response = {"success": success, "message": msg}
                
            elif action == "move":
                target = payload.get("target")
                success, msg = game.move(client_id, target)
                response = {"success": success, "message": msg}
            
            # 广播最新的游戏状态
            await manager.broadcast({"type": "state", "data": game.get_snapshot()})
            
            # 发送操作结果给当前用户（可选）
            # await websocket.send_json({"type": "response", "data": response})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        game.remove_player(client_id)
        await manager.broadcast({"type": "state", "data": game.get_snapshot()})
