from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from core.ui import BTN_LOGOUT

BTN_GROUPS = "👥 Guruhlarim"
BTN_DAILY = "📅 Kunlik davomat"
BTN_OVERALL = "📈 Umumiy davomat"


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_GROUPS)],
            [KeyboardButton(text=BTN_DAILY)],
            [KeyboardButton(text=BTN_OVERALL)],
            [KeyboardButton(text=BTN_LOGOUT)],
        ],
        resize_keyboard=True,
    )


def groups_keyboard(groups):
    buttons = [
        InlineKeyboardButton(text=g["name"], callback_data=f"g:{g['id']}")
        for g in groups
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text=BTN_OVERALL, callback_data="t_overall")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def semesters_keyboard(group_id, semesters):
    rows = [
        [InlineKeyboardButton(text=f"📚 {s['name']}", callback_data=f"gs:{group_id}:{s['id']}")]
        for s in semesters
    ]
    rows.append([InlineKeyboardButton(text="🔙 Guruhlar", callback_data="groups")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def actions_keyboard(group_id, semester_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍🎓 Talabalar bo'yicha", callback_data=f"gst:{group_id}:{semester_id}")],
            [InlineKeyboardButton(text="📊 Guruh bo'yicha umumiy", callback_data=f"gtt:{group_id}:{semester_id}")],
            [InlineKeyboardButton(text="🔙 Semestrlar", callback_data=f"g:{group_id}")],
        ]
    )


def overall_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Guruhlarni ko'rish", callback_data="groups")]
        ]
    )


def daily_groups_keyboard(groups):
    buttons = [
        InlineKeyboardButton(text=g["name"], callback_data=f"dg:{g['id']}")
        for g in groups
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def daily_days_keyboard(group_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugun", callback_data=f"dd:{group_id}:today"),
                InlineKeyboardButton(text="📅 Kecha", callback_data=f"dd:{group_id}:yesterday"),
            ],
            [InlineKeyboardButton(text="🗓 Oxirgi 7 kun", callback_data=f"dd:{group_id}:week")],
            [InlineKeyboardButton(text="✏️ Sana kiritish", callback_data=f"dd:{group_id}:custom")],
            [InlineKeyboardButton(text="🔙 Guruhlar", callback_data="dgroups")],
        ]
    )