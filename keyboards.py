from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

PROBLEM_TYPES = [
    "Компьютер/ноутбук",
    "Принтер",
    "Этикет-принтер",
    "Сканер/ТСД",
    "Сеть/интернет",
    "1С/программное обеспечение",
    "Другое",
]

PRIORITIES = ["Низкая", "Средняя", "Высокая"]

STATUSES = ["Новая", "В работе", "Выполнена", "Отменена"]

BTN_NEW_REQUEST = "📝 Создать заявку"
BTN_MY_REQUESTS = "📋 Мои заявки"
BTN_HELP = "❓ Помощь"
BTN_ALL_REQUESTS = "📂 Все заявки"
BTN_NEW_ONLY = "🆕 Новые заявки"
BTN_STATS = "📊 Статистика"

RESERVED_TEXTS = {
    BTN_NEW_REQUEST,
    BTN_MY_REQUESTS,
    BTN_HELP,
    BTN_ALL_REQUESTS,
    BTN_NEW_ONLY,
    BTN_STATS,
}


def user_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_NEW_REQUEST)
    builder.button(text=BTN_MY_REQUESTS)
    builder.button(text=BTN_HELP)
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def admin_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_NEW_REQUEST)
    builder.button(text=BTN_MY_REQUESTS)
    builder.button(text=BTN_HELP)
    builder.button(text=BTN_ALL_REQUESTS)
    builder.button(text=BTN_NEW_ONLY)
    builder.button(text=BTN_STATS)
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def problem_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, ptype in enumerate(PROBLEM_TYPES):
        builder.button(text=ptype, callback_data=f"ptype:{i}")
    builder.adjust(1)
    return builder.as_markup()


def priority_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for priority in PRIORITIES:
        builder.button(text=priority, callback_data=f"priority:{priority}")
    builder.adjust(3)
    return builder.as_markup()


def request_card_keyboard(scope: str, index: int, total: int, request_id: int) -> InlineKeyboardMarkup:
    """Кнопки карточки заявки: scope - раздел списка, index - позиция текущая,
    total — всего заявок в списке."""
    builder = InlineKeyboardBuilder()
    for status in STATUSES:
        builder.button(text=status, callback_data=f"setstatus:{scope}:{index}:{request_id}:{status}")
    builder.adjust(2)

    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"page:{scope}:{index - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data="noop"))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"page:{scope}:{index + 1}"))
    builder.row(*nav_row)

    return builder.as_markup()
