from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from states.dialog import DialogStates
from database.db import db
from utils.keyboards import get_main_keyboard, get_dialog_navigation_keyboard, get_admin_message_keyboard
from aiogram.utils.exceptions import MessageNotModified, BotBlocked
import json

with open('config.json', 'r') as f:
    config = json.load(f)


async def start_cmd(message: types.Message):
    await db.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    is_admin = message.from_user.id == config['ADMIN_ID']
    keyboard = get_main_keyboard(is_admin)

    await message.answer(
        "👋 Добро пожаловать в систему обратной связи!\n"
        "Выберите действие в меню ниже:",
        reply_markup=keyboard
    )


async def show_profile(callback_query: types.CallbackQuery):
    try:
        user_info = await db.get_user_info(callback_query.from_user.id)

        username = f"@{user_info['username']}" if user_info['username'] else "Отсутствует"

        profile_text = (
            f"👤 Ваш профиль:\n\n"
            f"📌 ID: {user_info['user_id']}\n"
            f"👤 Имя: {user_info['full_name']}\n"
            f"🔗 Username: {username}\n"
            f"📅 Дата регистрации: {user_info['registration_date']}"
        )

        current_text = callback_query.message.text

        if current_text != profile_text:
            await callback_query.message.edit_text(
                profile_text,
                reply_markup=get_main_keyboard(callback_query.from_user.id == config['ADMIN_ID'])
            )
    except BotBlocked:
        print(f"Ошибка: Не удалось показать профиль. Бот заблокирован пользователем {callback_query.from_user.id}")


async def show_dialog_history(callback_query: types.CallbackQuery):
    try:
        history = await db.get_dialog_history(callback_query.from_user.id, config['ADMIN_ID'])

        if not history:
            await callback_query.message.edit_text(
                "История диалогов пуста",
                reply_markup=get_main_keyboard(callback_query.from_user.id == config['ADMIN_ID'])
            )
            return

        history_text = "📋 История диалога:\n\n"
        for msg in history:
            direction = "📤" if msg['from_id'] == callback_query.from_user.id else "📥"
            history_text += f"{direction} {msg['message']}\n"
            history_text += f"Дата: {msg['date']}\n"
            history_text += "➖➖➖➖➖➖➖➖\n"

        current_text = callback_query.message.text

        if current_text != history_text:
            await callback_query.message.edit_text(
                history_text,
                reply_markup=get_main_keyboard(callback_query.from_user.id == config['ADMIN_ID'])
            )
    except MessageNotModified:
        await callback_query.answer()
    except BotBlocked:
        print(f"Ошибка: Не удалось показать историю диалогов. Бот заблокирован пользователем {callback_query.from_user.id}")


async def start_message(callback_query: types.CallbackQuery, state: FSMContext):
    if await db.is_user_blocked(callback_query.from_user.id):
        await callback_query.answer("Вы заблокированы в системе", show_alert=True)
        return

    await callback_query.message.edit_text(
        "📝 Введите ваше сообщение:",
        reply_markup=None
    )
    await DialogStates.waiting_for_message.set()


async def process_message(message: types.Message, state: FSMContext):
    if await db.is_user_blocked(message.from_user.id):
        await message.answer("Вы заблокированы в системе")
        return

    await db.add_message(
        from_id=message.from_user.id,
        to_id=config['ADMIN_ID'],
        message=message.text
    )

    await message.answer(
        "✅ Сообщение отправлено администратору",
        reply_markup=get_main_keyboard(message.from_user.id == config['ADMIN_ID'])
    )

    try:
        await message.bot.send_message(
            config['ADMIN_ID'],
            f"📨 Новое сообщение от @{message.from_user.username if message.from_user.username else 'Отсутствует'} (ID: {message.from_user.id}):\n\n{message.text}",
            reply_markup=get_admin_message_keyboard(message.from_user.id)
        )
    except BotBlocked:
        print(f"Ошибка: Не удалось отправить сообщение администратору. Бот заблокирован.")

    await state.finish()


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_callback_query_handler(show_profile, lambda c: c.data == 'profile')
    dp.register_callback_query_handler(show_dialog_history, lambda c: c.data == 'dialog_history')
    dp.register_callback_query_handler(start_message, lambda c: c.data == 'write_message')
    dp.register_message_handler(process_message, state=DialogStates.waiting_for_message)