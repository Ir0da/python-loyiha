from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from core.ui import BTN_LOGOUT

BTN_VIEW = "📊 Davomatni ko'rish"
BTN_DAILY = "📅 Kunlik davomat"
BTN_OVERALL = "📈 Umumiy davomat"


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_VIEW)],
            [KeyboardButton(text=BTN_DAILY)],
            [KeyboardButton(text=BTN_OVERALL)],
            [KeyboardButton(text=BTN_LOGOUT)],
        ],
        resize_keyboard=True,
    )


def semester_menu_keyboard(semesters):
    rows = [
        [InlineKeyboardButton(text=f"📚 {s['name']}", callback_data=f"sem:{s['id']}")]
        for s in semesters
    ]
    rows.append([InlineKeyboardButton(text=BTN_OVERALL, callback_data="overall")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def semester_actions_keyboard(semester_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Fanlar bo'yicha", callback_data=f"subjects:{semester_id}")],
            [InlineKeyboardButton(text="📊 Semestr bo'yicha umumiy", callback_data=f"semester_total:{semester_id}")],
            [InlineKeyboardButton(text="🔙 Semestrlar", callback_data="semesters")],
        ]
    )


def overall_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Semestrlarni ko'rish", callback_data="semesters")]
        ]
    )


def day_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Bugun", callback_data="day:today"),
                InlineKeyboardButton(text="📅 Kecha", callback_data="day:yesterday"),
            ],
            [InlineKeyboardButton(text="🗓 Oxirgi 7 kun", callback_data="day:week")],
            [InlineKeyboardButton(text="✏️ Sana kiritish", callback_data="day:custom")],
        ]
    )