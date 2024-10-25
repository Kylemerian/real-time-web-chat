from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update
from .models import *

async def userAdd(nickname: str, username: str, hashed_password: str, session: AsyncSession):
    user = User(nickname=nickname, username=username, hashed_password=hashed_password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user.id

async def userGetAll(session: AsyncSession):
    res = await session.scalars(select(User))
    return res.all()

async def userGetById(id: int, session: AsyncSession):
    res = await session.scalars(select(User).filter_by(User.id == id))
    res = res.scalar_one_or_none()
    return {"username": res.username, "hashed_password": res.hashed_password}

async def userGetByLogin(login: str, session: AsyncSession):
    res = await session.execute(select(User).filter_by(username = login))
    res = res.scalar_one_or_none()
    if res is None:
        return None
    else:
        return {"username": res.username, "hashed_password": res.hashed_password, "id": res.id}
    
def verifyPassword(passw: str, hashedPass: str):
    return passw == hashedPass
