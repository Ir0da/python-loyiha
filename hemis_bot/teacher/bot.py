import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.auth import build_auth_router
from core.config import TEACHER_BASE_URL, need
from core.db import init_db
from core.hemis import close_session
from . import ROLE, handlers_groups, handlers_overall
from .keyboards import main_keyboard
from . import ROLE, handlers_daily, handlers_groups, handlers_overall


async def main():
    init_db()

    bot = Bot(token=need("TEACHER_BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(
        build_auth_router(
            ROLE,
            TEACHER_BASE_URL,
            main_keyboard,
            "Assalomu alaykum, ustoz! 👋\n\nHEMIS loginingizni kiriting:",
        )
    )
    dp.include_router(handlers_daily.router)      # <-- auth'dan keyin
    dp.include_router(handlers_groups.router)
    dp.include_router(handlers_overall.router)

    print("🤖 O'qituvchi boti ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_session()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())