import asyncio
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.auth import build_auth_router
from core.config import BASE_URL, need
from core.db import init_db
from core.hemis import close_session
from . import ROLE, handlers_daily, handlers_overall, handlers_semester
from .keyboards import main_keyboard


# 🌐 Render serveri "Timed Out" xatosi bermasligi uchun soxta sahifa funksiyasi
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")


async def main():
    init_db()

    bot = Bot(token=need("STUDENT_BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(
        build_auth_router(
            ROLE,
            BASE_URL,
            main_keyboard,
            "Assalomu alaykum! 👋\n\nHEMIS loginingizni (ID raqamingizni) kiriting:",
        )
    )
    dp.include_router(handlers_daily.router)
    dp.include_router(handlers_semester.router)
    dp.include_router(handlers_overall.router)

    # 🚀 RENDER UCHUN SOXTA VEB-SERVERNI ISHGA TUSHIRISH QISMI:
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render avtomatik taqdim etadigan 10000-portni tinglaymiz
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print("🤖 O'quvchi boti ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_session()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
