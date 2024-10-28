from fastapi import WebSocket
from typing import Dict
from src.db.services import usrService
import redis
from src.db.config import *
from src.db.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.bot.celery_app import *


redis_client = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: dict, session: AsyncSession):
        if self.is_user_online(user_id):
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
            print(f"USER {user_id} online")
        else:
            print(f"USER {user_id} offline")
            usr = await usrService.userGetById(user_id, session)
            sender = await usrService.userGetById(message['sender_id'], session)
            if usr['tg_id']:
                # print(f"Send notif to tg: {user_id} {usr['tg_id']}")
                send_message_task.delay(usr['tg_id'], message, sender['nickname'])

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def get_connection(self, user_id: int) -> WebSocket:
        return self.active_connections.get(user_id)
    
    def is_user_online(self, user_id: int):
        return user_id in self.active_connections