from fastapi import APIRouter, status, Request, HTTPException, File, WebSocket, Depends, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from src.db.services import *
from src.db.db import *
import json
import jwt
from src.api.connectionManager import *
from src.db.config import SECRET_HASH
from datetime import datetime, timezone


router = APIRouter()
templates = Jinja2Templates(directory="templates")


manager = ConnectionManager()

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_HASH, algorithms=["HS256"])
        return payload.get("userId")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid JWT Token")


@router.get("/getUsers")
async def getUsers(request: Request, session: AsyncSession = Depends(get_async_session)):
    uid = verify_jwt(request.cookies.get("access_token"))
    users = await usrService.userGetAll(session)
    return users


@router.get("/app")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="app.html")


@router.get("/chats")
async def getChats(request: Request, session: AsyncSession = Depends(get_async_session)):
    uid = verify_jwt(request.cookies.get("access_token"))
    chats = await chatService.getUserChats(session, uid)  

    return chats

@router.post("/addChat")
async def add_chat(
    request: Request,
    # user_id_2: int,
    session: AsyncSession = Depends(get_async_session),
):
    uid = verify_jwt(request.cookies.get("access_token"))
    body = await request.json()
    user_id_2 = body.get("user_id")
    chat_id = await chatService.addChat(session, uid, user_id_2)

    return {"chat_id": chat_id}

@router.get("/getChats")
async def get_chats(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    uid = verify_jwt(request.cookies.get("access_token"))

    chats = await chatService.getUserChats(session, uid)

    return chats


@router.get("/chat/{chat_id}")
async def get_history(
    request: Request,
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    uid = verify_jwt(request.cookies.get("access_token"))
    chatMembers = await chatMmbrService.getChatMembersByChatId(session, chat_id)
    uids_set = {item['user_id'] for item in chatMembers}
    if uid in uids_set:
        msgs = await msgService.getMessagesByChatId(session, chat_id)
    else:
        msgs = []
    another_uid = (uids_set - {uid}).pop()
    return {'uid': uid, 'messages': msgs, 'isOnline': manager.is_user_online(another_uid)}

def get_current_user(request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, SECRET_HASH, algorithms=["HS256"])
        user_id = payload.get("userId")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session: AsyncSession = Depends(get_async_session)):
    user_id = get_current_user(websocket)
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            now_utc = datetime.now(timezone.utc)
            now_naive = now_utc.replace(tzinfo=None)
            message_id = await msgService.addMessage(data['chat_id'], user_id, data['content'], now_naive, session)
            receps = await chatMmbrService.getChatMembersByChatId(session, data['chat_id'])
            for recep in receps:
                await manager.send_message(recep['user_id'], {**data, 'isMyMessage': user_id == recep['user_id'], 'message_id': message_id, 'sender_id': user_id, 'time': datetime.now(timezone.utc).isoformat()}, session)  # Отправляем сообщение обратно пользователю
            # await manager.broadcast({**data, 'isMyMessage': user_id == # , 'message_id': message_id, 'sender_id': user_id, 'time': datetime.now(timezone.utc).isoformat()})  # Широковещательная отправка сообщения
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # await manager.broadcast(f"{user_id} left the chat")