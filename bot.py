import asyncio
import json
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers
from database.db import init_db

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as f:
    config = json.load(f)

bot = Bot(token=config['BOT_TOKEN'])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def main():
    await init_db()
    register_user_handlers(dp)
    register_admin_handlers(dp)
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())