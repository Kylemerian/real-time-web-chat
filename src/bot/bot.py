from celery import Celery
from aiogram import Bot
from db.config import TGBOTTOKEN
import asyncio

celery_app = Celery('tasks', broker='redis://localhost:6379/1')

bot = Bot(token=TGBOTTOKEN)

async def send_telegram_message(chat_id: int, text: str):
    await bot.send_message(chat_id, text)

@celery_app.task
def send_message_task(chat_id: int, text: str):
    try:
        asyncio.run(send_telegram_message(chat_id, text))
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")