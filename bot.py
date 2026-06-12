import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import start, upload, quiz
from database.db import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Сначала создаём таблицы в БД
    await init_db()
    print("✅ База данных готова!")

    # 2. Запускаем бота
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # 3. Подключаем все роутеры (порядок важен!)
    dp.include_router(start.router)
    dp.include_router(upload.router)
    dp.include_router(quiz.router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())