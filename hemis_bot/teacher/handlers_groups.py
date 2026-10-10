import asyncio

from aiogram import F, Router, types

from core.db import get_token
from core.ui import NEED_LOGIN, fail, reply
from core.utils import escape_text
from . import ROLE
from .api import get_groups, get_semesters, load_group_semester
from .keyboards import (
    BTN_GROUPS,
    actions_keyboard,
    groups_keyboard,
    semesters_keyboard,
)
from .reports import (
    build_group_summary,
    build_group_total_report,
    build_students_report,
)

router = Router()


async def show_groups(target, user_id, edit=False):
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
            "👥 <b>Guruhni tanlang</b>\n\nKerakli guruhni tanlang:",
            edit,
            reply_markup=groups_keyboard(groups),
        )
    except Exception as e:
        await fail(target, e, user_id, ROLE, edit)


@router.message(F.text == BTN_GROUPS)
async def on_groups_button(message: types.Message):
    await show_groups(message, message.from_user.id)


@router.callback_query(F.data == "groups")
async def on_groups(callback: types.CallbackQuery):
    await callback.answer()
    await show_groups(callback.message, callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("g:"))
async def on_group_selected(callback: types.CallbackQuery):
    await callback.answer()

    group_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    message = callback.message

    token = get_token(user_id, ROLE)
    if not token:
        await reply(message, NEED_LOGIN, True)
        return

    try:
        groups, semesters = await asyncio.gather(
            get_groups(token), get_semesters(token)
        )
        group = next((g for g in groups if g["id"] == group_id), None)
        if group is None:
            await reply(message, "⚠️ Guruh topilmadi.", True)
            return

        await reply(
            message,
            f"👥 <b>{escape_text(group['name'])}</b>\n\nSemestrni tanlang:",
            True,
            reply_markup=semesters_keyboard(group_id, semesters),
        )
    except Exception as e:
        await fail(message, e, user_id, ROLE, edit=True)


async def _group_view(callback, loading_text, build):
    await callback.answer()

    _, group_id, semester_id = callback.data.split(":")
    user_id = callback.from_user.id
    message = callback.message

    token = get_token(user_id, ROLE)
    if not token:
        await reply(message, NEED_LOGIN, True)
        return

    await reply(message, loading_text, True)

    try:
        group, semester, rows = await load_group_semester(
            token, group_id, semester_id
        )
        if group is None:
            await reply(message, "⚠️ Guruh yoki semestr topilmadi.", True)
            return

        await reply(
            message,
            build(group["name"], semester["name"], rows),
            True,
            reply_markup=actions_keyboard(group_id, semester_id),
        )
    except Exception as e:
        await fail(message, e, user_id, ROLE, edit=True)


@router.callback_query(F.data.startswith("gs:"))
async def on_group_semester(callback: types.CallbackQuery):
    await _group_view(
        callback, "⏳ Guruh davomati olinmoqda...", build_group_summary
    )


@router.callback_query(F.data.startswith("gst:"))
async def on_students(callback: types.CallbackQuery):
    await _group_view(
        callback, "⏳ Talabalar davomati olinmoqda...", build_students_report
    )


@router.callback_query(F.data.startswith("gtt:"))
async def on_group_total(callback: types.CallbackQuery):
    await _group_view(
        callback, "⏳ Guruh bo'yicha umumiy hisoblanmoqda...", build_group_total_report
    )