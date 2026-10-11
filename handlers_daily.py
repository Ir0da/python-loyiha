from datetime import timedelta

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.db import get_token
from core.timeutil import fmt_date, fmt_date_full, parse_user_date, today_uz
from core.ui import NEED_LOGIN, fail, reply
from . import ROLE
from .api import load_daily
from .keyboards import BTN_DAILY, day_keyboard
from .reports import build_daily_report

router = Router()

MENU_TEXT = "📅 <b>Kunlik davomat</b>\n\nQaysi davrni ko'rmoqchisiz?"


class DateState(StatesGroup):
    waiting_for_date = State()


def _range(kind):
    today = today_uz()
    if kind == "today":
        return today, today, f"Bugun — {fmt_date_full(today)}"
    if kind == "yesterday":
        day = today - timedelta(days=1)
        return day, day, f"Kecha — {fmt_date_full(day)}"
    start = today - timedelta(days=6)
    return start, today, f"Oxirgi 7 kun ({fmt_date(start)} — {fmt_date(today)})"


async def show_range(target, user_id, start, end, title, edit=False):
    token = get_token(user_id, ROLE)
    if not token:
        await reply(target, NEED_LOGIN, edit)
        return

    box = target
    try:
        loading = "⏳ Davomat tekshirilmoqda..."
        if edit:
            await reply(target, loading, True)
        else:
            box = await reply(target, loading)

        rows = await load_daily(token, start, end)
        await reply(
            box,
            build_daily_report(title, rows),
            True,
            reply_markup=day_keyboard(),
        )
    except Exception as e:
        await fail(box, e, user_id, ROLE, edit=True)


@router.message(F.text == BTN_DAILY)
async def on_daily_button(message: types.Message, state: FSMContext):
    await state.clear()
    await reply(message, MENU_TEXT, reply_markup=day_keyboard())


@router.callback_query(F.data.startswith("day:"))
async def on_day_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    kind = callback.data.split(":", 1)[1]

    if kind == "custom":
        await state.set_state(DateState.waiting_for_date)
        await reply(
            callback.message,
            "✏️ Sanani yuboring.\n\nMasalan: <code>08.10.2026</code> "
            "yoki <code>08.10</code>\n\nBekor qilish: /start",
            True,
        )
        return

    start, end, title = _range(kind)
    await show_range(
        callback.message, callback.from_user.id, start, end, title, edit=True
    )


@router.message(DateState.waiting_for_date)
async def on_date_entered(message: types.Message, state: FSMContext):
    day = parse_user_date(message.text)
    if day is None:
        await message.answer(
            "❌ Sana noto'g'ri. Masalan: 08.10.2026\n\nBekor qilish: /start"
        )
        return

    if day > today_uz():
        await message.answer("❌ Kelajak sanasini ko'ra olmayman. Boshqa sana kiriting.")
        return

    await state.clear()
    await show_range(
        message, message.from_user.id, day, day, fmt_date_full(day)
    )

    