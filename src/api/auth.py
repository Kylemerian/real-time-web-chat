from fastapi import Form, Depends, HTTPException, APIRouter, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import datetime
from db.config import SECRET_HASH
from db.services import *
from db.db import *

router = APIRouter()


def login_form_auth(
    logn: str = Form(...),
    password: str = Form(...)
) -> User:
    return User(username=logn, nickname=logn, hashed_password=password)

def login_form_reg(
    logn: str = Form(...),
    nick: str = Form(...),
    password: str = Form(...)
) -> User:
    return User(username=logn, nickname=nick, hashed_password=password)


@router.post("/login")
async def login(
    user: User = Depends(login_form_auth),
    session: AsyncSession=Depends(get_async_session)
):
    usr = await UserService.userGetByLogin(user.username, session)
    if not usr or not UserService.verifyPassword(user.hashed_password, usr['hashed_password']):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    token = jwt.encode({"sub": user.username, "userId": usr['id'], "nick": user.nickname, "exp": datetime.datetime.now() + datetime.timedelta(minutes=1440)}, SECRET_HASH, algorithm="HS256")
    response = RedirectResponse(url="/app", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=token, 
        # httponly=True,
        httponly=False,
        max_age=1440 * 60,
        expires=1440 * 60, 
        # secure=True,
        samesite="lax"
    )
    return response

@router.post("/register")
async def register(
    user: User = Depends(login_form_reg),
    session: AsyncSession=Depends(get_async_session)
):
    res = await UserService.userAdd(user.nickname, user.username, user.hashed_password, session)
    return RedirectResponse(url="/", status_code=302)