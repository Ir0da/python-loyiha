from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from .db import delete_user, get_token, save_user
from .hemis import ApiError, clear_cache, login as hemis_login
from .ui import BTN_LOGOUT


class LoginState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()


def build_auth_router(role, base_url, main_keyboard, greeting):
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()

        if get_token(message.from_user.id, role):
            await message.answer(
                "Siz allaqachon tizimga kirgansiz.\n\nKerakli amalni tanlang:",
                reply_markup=main_keyboard(),
            )
            return

        await message.answer(greeting)
        await state.set_state(LoginState.waiting_for_login)

    @router.message(LoginState.waiting_for_login)
    async def process_login(message: types.Message, state: FSMContext):
        login_name = (message.text or "").strip()
        if not login_name:
            await message.answer("❌ Login bo'sh bo'lmasligi kerak.")
            return

        await state.update_data(login=login_name)
        await message.answer("Endi HEMIS parolingizni kiriting:")
        await state.set_state(LoginState.waiting_for_password)

    @router.message(LoginState.waiting_for_password)
    async def process_password(message: types.Message, state: FSMContext):
        data = await state.get_data()
        login_name = data.get("login")
        password = (message.text or "").strip()

        # Parol chatda qolib ketmasligi uchun o'chiramiz
        try:
            await message.delete()
        except Exception:
            pass

        if not login_name or not password:
            await state.clear()
            await message.answer("❌ Login yoki parol kiritilmagan.\n/start ni bosing.")
            return

        wait = await message.answer("⏳ Tizimga ulanmoqda, iltimos kuting...")

        try:
            token = await hemis_login(base_url, login_name, password)
        except ApiError as e:
            await state.clear()
            await wait.edit_text(f"❌ {e}\n\nQaytadan /start ni bosing.")
            return

        await state.clear()

        if not token:
            await wait.edit_text(
                "❌ Login yoki parol noto'g'ri yoki server xatoligi.\n\n"
                "Qaytadan /start ni bosing."
            )
            return

        save_user(message.from_user.id, role, login_name, token)
        await wait.delete()
        await message.answer(
            "✅ Muvaffaqiyatli kirdingiz!", reply_markup=main_keyboard()
        )

    @router.message(F.text == BTN_LOGOUT)
    async def process_logout(message: types.Message):
        token = get_token(message.from_user.id, role)
        if token:
            clear_cache(token)
        delete_user(message.from_user.id, role)

        await message.answer(
            "🚪 Hisobdan chiqdingiz.\n\nQaytadan kirish uchun /start ni bosing.",
            reply_markup=ReplyKeyboardRemove(),
        )

    return router