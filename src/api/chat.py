from fastapi import APIRouter, status, Request, HTTPException, File, WebSocket, Depends, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from src.db.services import *
from src.db.db import *
import json
import jwt
from src.api.connectionManager import *
from src.db.config import SECRET_HASH
from datetime import datetime, timezone
import redis


router = APIRouter()
templates = Jinja2Templates(directory="templates")
redis_client = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)

manager = ConnectionManager()

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_HASH, algorithms=["HS256"])
        return payload.get("userId")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid JWT Token")

def json_serial(obj):
    """
    Serialize `datetime` obj into str
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


@router.get("/getUsers")
async def getUsers(request: Request, session: AsyncSession = Depends(get_async_session)):
    """
    Endpoint to get user list

    Args:
        request (Request): request
        session (AsyncSession, optional): connection to database

    Returns:
        list: list of dicts containing user info
    """
    uid = verify_jwt(request.cookies.get("access_token"))
    users = await usrService.userGetAll(session)
    return users


@router.get("/app")
async def root(request: Request):
    """
    Endpoint to main page of web chat

    Args:
        request (Request): request

    Returns:
        _TemplateResponse: page of web chat
    """
    return templates.TemplateResponse(request=request, name="app.html")


@router.post("/addChat")
async def add_chat(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Endpoint to create new chat

    Args:
        request (Request): request
        session (AsyncSession, optional): connection to database

    Returns:
        dict: dict containing chat_id of new chat
    """
    uid = verify_jwt(request.cookies.get("access_token"))
    body = await request.json()
    user_id_2 = body.get("user_id")
    chat_id = await chatService.addChat(session, uid, user_id_2)
    redis_client.delete(f"user_chats:{uid}")
    return {"chat_id": chat_id}


@router.get("/getChats")
async def get_chats(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Endpoint to get list of user chat

    Args:
        request (Request): request
        session (AsyncSession, optional): connection to database

    Returns:
        list: list of dicts containing chat info
    """
    uid = verify_jwt(request.cookies.get("access_token"))
    cache_key = f"user_chats:{uid}"

    cached_chats = redis_client.get(cache_key)
    if cached_chats:
        return json.loads(cached_chats)

    chats = await chatService.getUserChats(session, uid)
    redis_client.setex(cache_key, 300, json.dumps(chats, default=json_serial))
    return chats


@router.get("/chat/{chat_id}")
async def get_history(
    request: Request,
    chat_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Endpoint to get history of messages

    Args:
        request (Request): request
        chat_id (int): chat id
        session (AsyncSession, optional): connection to database

    Returns:
        dict: uid, online status, uid of another participant, list of messages
    """
    uid = verify_jwt(request.cookies.get("access_token"))
    cache_key = f"chat_history:{chat_id}"

    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        data = json.loads(cached_data)
        msgs = data['messages']
        another_uid = data.get('another_uid')
    else:
        chatMembers = await chatMmbrService.getChatMembersByChatId(session, chat_id)
        uids_set = {item['user_id'] for item in chatMembers}
        
        if uid in uids_set:
            msgs = await msgService.getMessagesByChatId(session, chat_id)
            another_uid = (uids_set - {uid}).pop() if uids_set - {uid} else None
            
            redis_client.setex(cache_key, 300, json.dumps({'messages': msgs, 'another_uid': another_uid}, default=json_serial))
        else:
            msgs = []
            another_uid = None

    result = {
        'uid': uid,
        'messages': msgs,
        'isOnline': manager.is_user_online(another_uid) if another_uid else False,
        'another_uid': another_uid
    }
    
    return result

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
    """
    Endpoint to exchange messages

    Args:
        websocket (WebSocket): websocket connection
        session (AsyncSession, optional): connection to database
    """
    user_id = get_current_user(websocket)
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            now_utc = datetime.now(timezone.utc)
            now_naive = now_utc.replace(tzinfo=None)
            message_id = await msgService.addMessage(data['chat_id'], user_id, data['content'], now_naive, session)
            receps = await chatMmbrService.getChatMembersByChatId(session, data['chat_id'])
            cache_key = f"chat_history:{data['chat_id']}"
            redis_client.delete(cache_key)
            for recep in receps:
                await manager.send_message(recep['user_id'], {**data, 'isMyMessage': user_id == recep['user_id'], 'message_id': message_id, 'sender_id': user_id, 'time': datetime.now(timezone.utc).isoformat()}, session)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # await manager.broadcast(f"{user_id} left the chat")