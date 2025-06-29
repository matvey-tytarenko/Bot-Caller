import os
import json
from aiogram import Bot, Dispatcher, types
import asyncio

TOKEN = os.environ.get("TELEGRAM_BOT_API")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработка /start
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Я бот на aiogram + Vercel!")

# Обработка обычных сообщений
@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")

def handler(request, response):
    try:
        # Преобразуем тело запроса в Update
        update_data = json.loads(request.body)
        update = types.Update(**update_data)

        # Обработка обновления через Dispatcher
        asyncio.run(dp.feed_update(bot, update))

        response.status_code = 200
        response.body = "ok"
    except Exception as e:
        print("❌ Ошибка:", e)
        response.status_code = 500
        response.body = "error"
    return response