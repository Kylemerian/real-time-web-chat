from celery import Celery
from aiogram import Bot, types
from aiogram.enums import ParseMode
from celery import shared_task
import asyncio
from datetime import datetime
from aiogram import Dispatcher
from db.config import *
from aiogram import F
from aiogram.filters import Command

bot = Bot(token=TGBOTTOKEN)
dp = Dispatcher()
app = Celery('tasks', broker=f"redis://{REDIS_HOST}:6379/1")
app.autodiscover_tasks(['bot'])


def run_async(coro):
    """Runs an asynchronous routine in a synchronous context"""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        return loop.run_until_complete(coro)

@shared_task
def send_message_task(chat_id, message, sender_nick):
    try:
        content = message['content']
        time = message['time']
        dt_time = datetime.fromisoformat(time)
        formatted_date = dt_time.strftime("%d-%m-%Y %H:%M")
        run_async(bot.send_message(chat_id, f"Sender: {sender_nick}\nMessage: {content}\nDate: {formatted_date}", parse_mode=ParseMode.HTML))
    except Exception as e:
        print(f"Failed to send message to {chat_id}: {e}")
        
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"Добро пожаловать в бота!\n"
        f"Ваш chat_id: {message.chat.id}\n"
        "Добавьте его в приложении в меню сверху."
        "Этот бот отправляет уведомления о новых сообщениях, когда Вы не в сети.\n"
    )


async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())