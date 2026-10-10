from aiogram import F, Router, types

from core.db import get_token
from core.ui import NEED_LOGIN, fail, reply
from . import ROLE
from .api import load_overall
from .keyboards import BTN_OVERALL, overall_keyboard
from .reports import build_overall_report

router = Router()

LOADING = "⏳ Barcha semestrlar bo'yicha davomat hisoblanmoqda...\n\nIltimos kuting."


async def show_overall(target, user_id, edit=False):
    token = get_token(user_id, ROLE)
    if not token:
        await reply(target, NEED_LOGIN, edit)
        return

    box = target
    try:
        if edit:
            await reply(target, LOADING, True)
        else:
            box = await reply(target, LOADING)

        reports = await load_overall(token)

        await reply(
            box,
            build_overall_report(reports),
            True,
            reply_markup=overall_keyboard(),
        )
    except Exception as e:
        await fail(box, e, user_id, ROLE, edit=True)


@router.message(F.text == BTN_OVERALL)
async def on_overall_button(message: types.Message):
    await show_overall(message, message.from_user.id)


@router.callback_query(F.data == "overall")
async def on_overall_callback(callback: types.CallbackQuery):
    await callback.answer()
    await show_overall(callback.message, callback.from_user.id, edit=True)