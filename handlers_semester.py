from aiogram import F, Router, types

from core.db import get_token
from core.ui import NEED_LOGIN, fail, reply
from . import ROLE
from .api import get_semesters, load_selected_semester
from .keyboards import BTN_VIEW, semester_actions_keyboard, semester_menu_keyboard
from .reports import (
    build_semester_summary,
    build_semester_total_report,
    build_subject_report,
)

router = Router()


async def show_semesters(target, user_id, edit=False):
    token = get_token(user_id, ROLE)
    if not token:
        await reply(target, NEED_LOGIN, edit)
        return

    try:
        semesters = await get_semesters(token)
        if not semesters:
            await reply(target, "⚠️ Semestrlar topilmadi.", edit)
            return

        await reply(
            target,
            "📚 <b>Semestrni tanlang</b>\n\nKerakli semestrni tanlang:",
            edit,
            reply_markup=semester_menu_keyboard(semesters),
        )
    except Exception as e:
        await fail(target, e, user_id, ROLE, edit)


@router.message(F.text == BTN_VIEW)
async def on_view_button(message: types.Message):
    await show_semesters(message, message.from_user.id)


@router.callback_query(F.data == "semesters")
async def on_semesters(callback: types.CallbackQuery):
    await callback.answer()
    await show_semesters(callback.message, callback.from_user.id, edit=True)


async def _semester_view(callback, loading_text, build):
    await callback.answer()

    semester_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    message = callback.message

    token = get_token(user_id, ROLE)
    if not token:
        await reply(message, NEED_LOGIN, True)
        return

    await reply(message, loading_text, True)

    try:
        selected, subjects = await load_selected_semester(token, semester_id)
        if selected is None:
            await reply(message, "⚠️ Tanlangan semestr topilmadi.", True)
            return

        await reply(
            message,
            build(selected["name"], subjects),
            True,
            reply_markup=semester_actions_keyboard(semester_id),
        )
    except Exception as e:
        await fail(message, e, user_id, ROLE, edit=True)


@router.callback_query(F.data.startswith("sem:"))
async def on_semester_selected(callback: types.CallbackQuery):
    await _semester_view(
        callback,
        "⏳ Semestrdagi fanlar va davomat olinmoqda...",
        build_semester_summary,
    )


@router.callback_query(F.data.startswith("subjects:"))
async def on_subjects(callback: types.CallbackQuery):
    await _semester_view(
        callback,
        "⏳ <b>Semestrdagi barcha fanlar olinmoqda...</b>",
        build_subject_report,
    )


@router.callback_query(F.data.startswith("semester_total:"))
async def on_semester_total(callback: types.CallbackQuery):
    await _semester_view(
        callback,
        "⏳ Semestr bo'yicha umumiy davomat hisoblanmoqda...",
        build_semester_total_report,
    )