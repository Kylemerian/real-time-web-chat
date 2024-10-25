from db.crud import *
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    async def userGetById(self, uid: int, session: AsyncSession):
        return await userGetById(uid, session)
    
    async def userAdd(self, nickname: str, username: str, hashed_password: str, session: AsyncSession):
        if await userGetByLogin(username, session):
            return -1
        return await userAdd(nickname, username, hashed_password, session)
    
    async def userGetAll(self, session: AsyncSession):
        return await userGetAll(session)
    
    def verifyPassword(self, pass1, pass2):
        return verifyPassword(pass1, pass2)
    
    async def userGetByLogin(self, login: str, session: AsyncSession):
        return await userGetByLogin(login, session)