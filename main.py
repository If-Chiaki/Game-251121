from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import uuid
from typing import List, Dict
from game_core import game

app = FastAPI()

# 挂载静态文件，用于访问 index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return FileResponse('static/index.html')

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def broadcast_game_state(self):
        for client_id, websocket in self.active_connections.items():
            try:
                # 为每个玩家生成专属的快照（应用迷雾）
                snapshot = game.get_snapshot(observer_id=client_id)
                await websocket.send_json({"type": "state", "data": snapshot})
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        # 发送初始状态
        await websocket.send_json({"type": "state", "data": game.get_snapshot(observer_id=client_id)})
        
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

            elif action == "pick_up":
                item_id = payload.get("item_id")
                success, msg = game.pick_up(client_id, item_id)
                response = {"success": success, "message": msg}

            elif action == "drop_item":
                item_id = payload.get("item_id")
                success, msg = game.drop_item(client_id, item_id)
                response = {"success": success, "message": msg}

            elif action == "attack":
                target_id = payload.get("target_id")
                weapon_id = payload.get("weapon_id")
                success, msg = game.attack(client_id, target_id, weapon_id)
                response = {"success": success, "message": msg}

            elif action == "use_potion":
                potion_id = payload.get("potion_id")
                target_id = payload.get("target_id")
                is_group = payload.get("is_group", False)
                success, msg = game.use_potion(client_id, potion_id, target_id, is_group)
                response = {"success": success, "message": msg}

            elif action == "tame":
                success, msg = game.tame(client_id)
                response = {"success": success, "message": msg}
            
            # 广播最新的游戏状态
            await manager.broadcast_game_state()
            
            # 发送操作结果给当前用户（可选）
            # await websocket.send_json({"type": "response", "data": response})
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        game.remove_player(client_id)
        await manager.broadcast_game_state()
