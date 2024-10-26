from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)

    if not is_admin:
        keyboard.add(
            InlineKeyboardButton("📝 Написать сообщение", callback_data="write_message"),
            InlineKeyboardButton("📋 История диалогов", callback_data="dialog_history")
        )

    keyboard.add(InlineKeyboardButton("👤 Мой профиль", callback_data="profile"))

    if is_admin:
        keyboard.add(
            InlineKeyboardButton("👥 Все диалоги", callback_data="all_dialogs"),
            InlineKeyboardButton("🚫 Блокировка пользователя", callback_data="block_user")
        )

    return keyboard


def get_dialog_navigation_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []

    if current_page > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{current_page - 1}"))

    buttons.append(InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="current_page"))

    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{current_page + 1}"))

    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))

    return keyboard


def get_admin_message_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✍️ Ответить", callback_data=f"reply_{user_id}"),
    )
    return keyboard