from fastapi import Form, Depends, HTTPException, APIRouter, status, Request, Body
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import datetime
from src.db.config import SECRET_HASH
from src.db.services import *
from src.db.db import *
from src.api.chat import verify_jwt

router = APIRouter()


def login_form_auth(
    logn: str = Form(...),
    password: str = Form(...)
) -> User:
    """
    Helper for parsing data from form for Sign In

    Args:
        logn (str, optional): login of user
        password (str, optional): password of user

    Returns:
        User: object User filled data from args
    """
    return User(username=logn, nickname=logn, hashed_password=password)

def login_form_reg(
    logn: str = Form(...),
    nick: str = Form(...),
    password: str = Form(...)
) -> User:
    """
    Helper for parsing data from form for Sign Up

    Args:
        logn (str, optional): login of user
        logn (str, optional): nickname of user
        password (str, optional): password of user

    Returns:
        User: object User filled data from args
    """
    return User(username=logn, nickname=nick, hashed_password=password)


@router.post("/login")
async def login(
    user: User = Depends(login_form_auth),
    session: AsyncSession=Depends(get_async_session)
):
    """
    Endpoint for Sign In

    Args:
        user (User, optional): User object with filled data
        session (AsyncSession, optional): connection to database

    Returns:
        RedirectResponse: set JWT token into cookie and redirect user to main page (/app)
    """
    usr = await usrService.userGetByLogin(user.username, session)
    if not usr or not usrService.verifyPassword(user.hashed_password, usr['hashed_password']):
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
    """
    Endpoint for Sign Up

    Args:
        user (User, optional): User object with filled data
        session (AsyncSession, optional): connection to database

    Returns:
        RedirectResponse: redirect user to sign in page (/)
    """
    res = await usrService.userAdd(user.nickname, user.username, user.hashed_password, session)
    return RedirectResponse(url="/", status_code=302)


@router.post("/setTgId")
async def setTgId(
    request: Request,
    tgId: dict = Body(...),
    session: AsyncSession=Depends(get_async_session)
):
    """
    Set telegram chat id for user

    Args:
        request (Request): request
        tgId (int, optional): telegram chat id
        session (AsyncSession, optional): connection to database

    Returns:
        int: user id
    """
    uid = verify_jwt(request.cookies.get("access_token"))
    return await usrService.userSetTgId(uid, int(tgId['tgId']), session)