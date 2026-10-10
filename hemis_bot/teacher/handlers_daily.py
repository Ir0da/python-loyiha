from datetime import timedelta

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.db import get_token
from core.timeutil import fmt_date, fmt_date_full, parse_user_date, today_uz
from core.ui import NEED_LOGIN, fail, reply
from . import ROLE
from .api import get_groups, load_group_daily
from .keyboards import BTN_DAILY, daily_days_keyboard, daily_groups_keyboard
from .reports import build_daily_report

router = Router()


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


async def show_daily_groups(target, user_id, edit=False):
    token = get_token(user_id, ROLE)
    if not token:
        await reply(target, NEED_LOGIN, edit)
        return

    try:
        groups = await get_groups(token)
        if not groups:
            await reply(target, "⚠️ Guruhlar topilmadi.", edit)
            return

        await reply(
            target,
            "📅 <b>Kunlik davomat</b>\n\nGuruhni tanlang:",
            edit,
            reply_markup=daily_groups_keyboard(groups),
        )
    except Exception as e:
        await fail(target, e, user_id, ROLE, edit)


async def show_group_range(target, user_id, group_id, start, end, title, edit=False):
    token = get_token(user_id, ROLE)
    if not token:
        await reply(target, NEED_LOGIN, edit)
        return

    box = target
    try:
        loading = "⏳ Guruh davomati tekshirilmoqda..."
        if edit:
            await reply(target, loading, True)
        else:
            box = await reply(target, loading)

        group, rows = await load_group_daily(token, group_id, start, end)
        if group is None:
            await reply(box, "⚠️ Guruh topilmadi.", True)
            return

        await reply(
            box,
            build_daily_report(group["name"], title, rows),
            True,
            reply_markup=daily_days_keyboard(group_id),
        )
    except Exception as e:
        await fail(box, e, user_id, ROLE, edit=True)


@router.message(F.text == BTN_DAILY)
async def on_daily_button(message: types.Message, state: FSMContext):
    await state.clear()
    await show_daily_groups(message, message.from_user.id)


@router.callback_query(F.data == "dgroups")
async def on_daily_groups(callback: types.CallbackQuery):
    await callback.answer()
    await show_daily_groups(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("dg:"))
async def on_daily_group(callback: types.CallbackQuery):
    await callback.answer()
    group_id = callback.data.split(":", 1)[1]
    await reply(
        callback.message,
        "📅 <b>Kunlik davomat</b>\n\nQaysi davrni ko'rmoqchisiz?",
        True,
        reply_markup=daily_days_keyboard(group_id),
    )


@router.callback_query(F.data.startswith("dd:"))
async def on_daily_day(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    _, group_id, kind = callback.data.split(":")

    if kind == "custom":
        await state.set_state(DateState.waiting_for_date)
        await state.update_data(group_id=group_id)
        await reply(
            callback.message,
            "✏️ Sanani yuboring.\n\nMasalan: <code>08.10.2026</code> "
            "yoki <code>08.10</code>\n\nBekor qilish: /start",
            True,
        )
        return

    start, end, title = _range(kind)
    await show_group_range(
        callback.message, callback.from_user.id, group_id, start, end, title, edit=True
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

    data = await state.get_data()
    group_id = data.get("group_id")
    await state.clear()

    await show_group_range(
        message, message.from_user.id, group_id, day, day, fmt_date_full(day)
    )