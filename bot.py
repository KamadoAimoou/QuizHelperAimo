import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from handlers import start

async def main():
    bot = Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(start.router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot is starting ......")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())