from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from api import auth, chat

app = FastAPI()
app.mount("/templates", StaticFiles(directory="../templates", html=True), name='templates')
app.mount("/content", StaticFiles(directory="../content", html=True), name='content')

app.include_router(auth.router)
app.include_router(chat.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените на ваш домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="../templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="enter.html")

# @app.exception_handler(404)
# async def not_found_handler(request: Request, exc):
#     return templates.TemplateResponse(request=request, name="error.html")