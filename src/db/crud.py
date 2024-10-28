from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update, and_
from sqlalchemy.orm import aliased
from .models import *

async def userAdd(nickname: str, username: str, hashed_password: str, session: AsyncSession) -> int:
    """
    Add new user to database

    Args:
        nickname (str): nickname of new user
        username (str): login of new user
        hashed_password (str): encrypted password
        session (AsyncSession): connection to db

    Returns:
        int: id of created user
    """
    user = User(nickname=nickname, username=username, hashed_password=hashed_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id

async def userGetAll(session: AsyncSession):
    """
    Get list of all users

    Args:
        session (AsyncSession): connection to db

    Returns:
        list: list of dicts containing id and nickname for all users
    """
    result = await session.execute(select(User.id, User.nickname))
    users = result.fetchall()
    return [{"id": user.id, "nickname": user.nickname} for user in users]

async def userGetById(idd: int, session: AsyncSession):
    """
    Get user by its id

    Args:
        idd (int): user id
        session (AsyncSession): connection to db

    Returns:
        dict: dict containing username, nickname, encrypted password and telegram chat id for bot notification
    """
    res = await session.scalars(select(User).filter_by(id=idd))
    user = res.first()

    if user is None:
        return None

    return {
        "username": user.username,
        "nickname": user.nickname,
        "hashed_password": user.hashed_password,
        "tg_id": user.tg_id
    }

async def userGetByLogin(login: str, session: AsyncSession):
    """
    Get user by its login

    Args:
        login (str): login of user
        session (AsyncSession): connection to db

    Returns:
        dict: dict containing username, encrypted password and id
    """
    res = await session.execute(select(User).filter_by(username = login))
    res = res.scalar_one_or_none()
    if res is None:
        return None
    else:
        return {"username": res.username, "hashed_password": res.hashed_password, "id": res.id}
    
def verifyPassword(passw: str, hashedPass: str) -> bool:
    """
    Checks if encrypted password same to decrypted one

    Args:
        passw (str): decrypted password
        hashedPass (str): encrypted password

    Returns:
        bool: True, if same; False otherwise
    """
    return passw == hashedPass

async def userSetTgId(user_id:int, tgId: int, session: AsyncSession) -> int:
    """
    Set telegram chat id for user with user_id

    Args:
        user_id (int): user id
        tgId (int): telegram chat id
        session (AsyncSession): connection to db

    Returns:
        int: user id
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one()
    
    user.tg_id = tgId
    
    await session.commit()
    return user_id

async def addChat(session: AsyncSession, user_id: int, user_id2: int) -> int:
    """
    Add new chat for users with user_id and user_id2 to database

    Args:
        session (AsyncSession): connection to db
        user_id (int): id of first user
        user_id2 (int): id of second user

    Returns:
        int: id of created chat
    """
    existing_chat_query = (
        select(Chat)
        .join(ChatMembers)
        .filter(
            ChatMembers.user_id.in_([user_id, user_id2]),
            Chat.id == ChatMembers.chat_id
        )
        .group_by(Chat.id)
        .having(func.count() > 1)
    )

    existing_chat = await session.execute(existing_chat_query)
    chat = existing_chat.scalar()

    if chat:
        return chat.id
    newChat = Chat(chat_name = ".")
    session.add(newChat)
    await session.flush()
    
    chat_members = [ChatMembers(chat_id=newChat.id, user_id=user_id) for user_id in [user_id, user_id2]]
    session.add_all(chat_members)
    await session.commit()
    return newChat.id


async def addMessage(session: AsyncSession, chat_id: int, user_id:int, message: str, time: DateTime) -> int:
    """
    Add new message to database

    Args:
        session (AsyncSession): connection to db
        chat_id (int): chat id where message was sent
        user_id (int): sender id
        message (str): content of message
        time (DateTime): date + time when message was sent

    Returns:
        int: message id
    """
    newMessage = Message(chat_id=chat_id, sender_id=user_id, text=message, time=time)
    session.add(newMessage)
    await session.commit()
    await session.refresh(newMessage)
    return newMessage.id


async def getUserChats(session: AsyncSession, user_id: int):
    """
    Get list of user chats by user id

    Args:
        session (AsyncSession): connection to db
        user_id (int): user id which chats returns

    Returns:
        list: list of dicts containing chat id, name of another user in chat, last message content and last message time
    """
    chat_ids_subquery = (
        select(ChatMembers.chat_id)
        .where(ChatMembers.user_id == user_id)
        .subquery()
    )

    chat_members_subquery = (
        select(ChatMembers.chat_id, ChatMembers.user_id)
        .where(ChatMembers.chat_id.in_(chat_ids_subquery))
        .where(ChatMembers.user_id != user_id)
        .subquery()
    )

    last_message_subquery = (
        select(
            Message.chat_id,
            func.max(Message.time).label('last_message_time')
        )
        .group_by(Message.chat_id)
        .subquery()
    )

    query = (
        select(
            chat_members_subquery.c.chat_id,
            # User.avatar_url.label('avatar'),
            User.nickname.label('participant_name'),
            Message.text.label('last_message_text'),
            last_message_subquery.c.last_message_time
        )
        .select_from(chat_members_subquery)
        .outerjoin(
            last_message_subquery,
            chat_members_subquery.c.chat_id == last_message_subquery.c.chat_id
        )
        .outerjoin(
            Message,
            and_(
                Message.chat_id == chat_members_subquery.c.chat_id,
                Message.time == last_message_subquery.c.last_message_time
            )
        )
        .join(
            User,
            User.id == chat_members_subquery.c.user_id
        )
    )
    
    
    result = await session.execute(query)
    # columns = [column.name for column in query.columns]
    rows = result.fetchall()

    chat_list = [
        {
            'chat_id': row.chat_id,
            # 'avatar': row.avatar,
            'participant_name': row.participant_name,
            'last_message_text': row.last_message_text,
            'last_message_time': row.last_message_time
        }
        for row in rows
    ]
    
    return chat_list


async def getMessagesByChatId(session: AsyncSession, chat_id: int):
    """
    Get list of messages by chat id

    Args:
        session (AsyncSession): connection to db
        chat_id (int): chat id which messages returns

    Returns:
        list: list of dicts containing message info
    """
    query = select(Message).where(Message.chat_id == chat_id).order_by(Message.time)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    message_list = [
        {
            'message_id': row.Message.id,
            'chat_id': row.Message.chat_id,
            'sender_id': row.Message.sender_id,
            'text': row.Message.text,
            'time': row.Message.time.isoformat()
        }
        for row in rows
    ]
    
    return message_list

async def getChatMembersByChatId(session: AsyncSession, chat_id: int):
    """
    Get members of chat by chat id

    Args:
        session (AsyncSession): connection to db
        chat_id (int): chat id which members returns

    Returns:
        list: list of dict containing user ids of members
    """
    query = select(ChatMembers).where(ChatMembers.chat_id == chat_id)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    user_list = [
        {
            'user_id': row.ChatMembers.user_id
        }
        for row in rows
    ]
    
    return user_list

async def isExistChatByUserIds(session: AsyncSession, user_id:int, user_id2: int):
    """
    Checks if chat with user_id and user_id2 already exists

    Args:
        session (AsyncSession): connection to db
        user_id (int): first user id
        user_id2 (int): second user id

    Returns:
        int or None: chat id or None if chat doesn't exist
    """
    member1 = aliased(ChatMembers)
    member2 = aliased(ChatMembers)
    
    stmt = (
        select(member1.chat_id)
        .join(member2, member1.chat_id == member2.chat_id)
        .where(member1.user_id == user_id)
        .where(member2.user_id == user_id2)
    )
    
    result = await session.execute(stmt)
    chat_id = result.scalar()

    return chat_id is not None