from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from states.dialog import DialogStates
from database.db import db
from utils.keyboards import get_main_keyboard, get_dialog_navigation_keyboard, get_admin_message_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified, BotBlocked
import json

with open('config.json', 'r') as f:
    config = json.load(f)


async def show_all_dialogs(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        if callback_query.from_user.id != config['ADMIN_ID']:
            await callback_query.answer("Недостаточно прав", show_alert=True)
            return

        current_page = (await state.get_data()).get("current_page", 1)

        dialogs = await db.get_all_dialogs(config['ADMIN_ID'])

        total_pages = (len(dialogs) + 9) // 10

        if current_page < 1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages

        start_index = (current_page - 1) * 10
        end_index = min(start_index + 10, len(dialogs))
        page_dialogs = dialogs[start_index:end_index]

        keyboard = InlineKeyboardMarkup(row_width=2)
        for dialog in page_dialogs:
            keyboard.add(
                InlineKeyboardButton(
                    f"{dialog['full_name']} (@{dialog['username'] if dialog['username'] else 'Отсутствует'})",
                    callback_data=f"dialog_{dialog['user_id']}"
                )
            )

        if total_pages > 1:
            navigation_buttons = []
            if current_page > 1:
                navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{current_page - 1}"))
            navigation_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))
            if current_page < total_pages:
                navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{current_page + 1}"))
            keyboard.add(*navigation_buttons)

        keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))

        await state.update_data({"current_page": current_page})

        await callback_query.message.edit_text(
            "📋 Список диалогов:",
            reply_markup=keyboard
        )
    except MessageNotModified:
        await callback_query.answer()
    except BotBlocked:
        print(f"Ошибка: Не удалось показать список диалогов. Бот заблокирован пользователем {callback_query.from_user.id}")


async def process_page_change(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        page = int(callback_query.data.split('_')[1])
        await state.update_data({"current_page": page})
        await show_all_dialogs(callback_query, state)
    except BotBlocked:
        print(f"Ошибка: Не удалось изменить страницу. Бот заблокирован пользователем {callback_query.from_user.id}")


async def ignore_callback(callback_query: types.CallbackQuery):
    try:
        await callback_query.answer()
    except BotBlocked:
        print(f"Ошибка: Не удалось ответить на callback. Бот заблокирован пользователем {callback_query.from_user.id}")


async def show_dialog(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_id = int(callback_query.data.split('_')[1])
        history = await db.get_dialog_history(user_id, config['ADMIN_ID'])

        if not history:
            await callback_query.answer("Диалог пуст", show_alert=True)
            return

        history_text = f"📋 Диалог с пользователем {user_id}:\n\n"
        for msg in history:
            direction = "Админ:" if msg['from_id'] == config['ADMIN_ID'] else "Пользователь:"
            history_text += f"{direction} {msg['message']}\n"
            history_text += f"Дата: {msg['date']}\n"
            history_text += "➖➖➖➖➖➖➖➖\n"

        await callback_query.message.edit_text(
            history_text,
            reply_markup=get_main_keyboard(is_admin=True)
        )

        await state.update_data(reply_to=user_id)
    except BotBlocked:
        print(f"Ошибка: Не удалось показать диалог. Бот заблокирован пользователем {callback_query.from_user.id}")


async def reply_to_user(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        if callback_query.from_user.id != config['ADMIN_ID']:
            await callback_query.answer("Недостаточно прав", show_alert=True)
            return

        user_id = int(callback_query.data.split('_')[1])
        await state.update_data(reply_to=user_id)

        await callback_query.message.edit_text(
            "✍️ Введите ваш ответ:",
            reply_markup=None
        )
        await DialogStates.waiting_for_reply.set()
    except BotBlocked:
        print(f"Ошибка: Не удалось ответить пользователю. Бот заблокирован пользователем {callback_query.from_user.id}")


async def process_admin_reply(message: types.Message, state: FSMContext):
    if message.from_user.id != config['ADMIN_ID']:
        return

    data = await state.get_data()
    user_id = data.get('reply_to')

    await db.add_message(
        from_id=config['ADMIN_ID'],
        to_id=user_id,
        message=message.text
    )

    await message.answer(
        "✅ Ответ отправлен",
        reply_markup=get_main_keyboard(True)
    )

    try:
        await message.bot.send_message(
            user_id,
            f"📨 Ответ от администратора:\n\n{message.text}",
            reply_markup=get_main_keyboard(False)
        )
    except BotBlocked:
        print(f"Ошибка: Не удалось отправить ответ пользователю {user_id}. Бот заблокирован.")

    await state.finish()

def register_admin_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(show_all_dialogs, lambda c: c.data == 'all_dialogs', state="*")
    dp.register_callback_query_handler(process_page_change, lambda c: c.data.startswith('page_'), state="*")
    dp.register_callback_query_handler(ignore_callback, lambda c: c.data == 'ignore', state="*")
    dp.register_callback_query_handler(show_dialog, lambda c: c.data.startswith('dialog_'))
    dp.register_callback_query_handler(reply_to_user, lambda c: c.data.startswith('reply_'))
    dp.register_message_handler(process_admin_reply, state=DialogStates.waiting_for_reply)