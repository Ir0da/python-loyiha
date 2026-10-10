from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardRemove

from .db import delete_user
from .hemis import TokenExpired
from .utils import escape_text

BTN_LOGOUT = "🚪 Hisobdan chiqish"
NEED_LOGIN = "⚠️ Avval tizimga kiring: /start"


async def reply(target, text, edit=False, **kwargs):
    """edit=True bo'lsa xabarni tahrirlaydi, aks holda yangi xabar yuboradi."""
    kwargs.setdefault("parse_mode", "HTML")

    if not edit:
        return await target.answer(text, **kwargs)

    try:
        return await target.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def fail(target, exc, user_id, role, edit=False):
    if isinstance(exc, TokenExpired):
        delete_user(user_id, role)
        text = "❌ Token eskirgan.\n\nIltimos, /start orqali qayta kiring."
        kwargs = {} if edit else {"reply_markup": ReplyKeyboardRemove()}
    else:
        text = f"❌ Xatolik yuz berdi:\n{escape_text(exc)}"
        kwargs = {}
    await reply(target, text, edit, **kwargs)