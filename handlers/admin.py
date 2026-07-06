from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import utils
from config import ADMIN_ID

router = Router()

SCOPE_STATUS_FILTER = {
    "all": None,
    "new": "Новая",
}

SCOPE_EMPTY_TEXT = {
    "all": "Заявок пока нет.",
    "new": "Новых заявок нет.",
}


def admin_only(telegram_id: int) -> bool:
    return telegram_id == ADMIN_ID


def format_request_full(r: dict) -> str:
    author = utils.user_link(r["telegram_id"], r.get("username"), r["full_name"])
    return (
        f"Заявка №{r['id']}\n"
        f"Статус: {r['status']}\n"
        f"Автор: {author}\n"
        f"ФИО: {utils.esc(r['full_name'])}\n"
        f"Подразделение: {utils.esc(r['department'])}\n"
        f"Тип проблемы: {utils.esc(r['problem_type'])}\n"
        f"Срочность: {utils.esc(r['priority'])}\n"
        f"Описание: {utils.esc(r['description'])}\n"
        f"Создана: {r['created_at']}\n"
        f"Обновлена: {r['updated_at']}"
    )


async def render_card(scope: str, index: int):
    status_filter = SCOPE_STATUS_FILTER[scope]
    requests = await db.get_all_requests(status=status_filter)
    if not requests:
        return None, None

    index = max(0, min(index, len(requests) - 1))
    r = requests[index]
    text = format_request_full(r)
    keyboard = kb.request_card_keyboard(scope, index, len(requests), r["id"])
    return text, keyboard


@router.message(F.text == kb.BTN_ALL_REQUESTS)
async def all_requests(message: Message, state: FSMContext) -> None:
    if not admin_only(message.from_user.id):
        return
    await state.clear()
    text, keyboard = await render_card("all", 0)
    if text is None:
        await message.answer(SCOPE_EMPTY_TEXT["all"])
        return
    await message.answer(text, reply_markup=keyboard)


@router.message(F.text == kb.BTN_NEW_ONLY)
async def new_requests(message: Message, state: FSMContext) -> None:
    if not admin_only(message.from_user.id):
        return
    await state.clear()
    text, keyboard = await render_card("new", 0)
    if text is None:
        await message.answer(SCOPE_EMPTY_TEXT["new"])
        return
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("page:"))
async def paginate(callback: CallbackQuery) -> None:
    if not admin_only(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    _, scope, index_str = callback.data.split(":")
    text, keyboard = await render_card(scope, int(index_str))
    if text is None:
        await callback.message.edit_text(SCOPE_EMPTY_TEXT.get(scope, "Заявок нет."))
        await callback.answer()
        return
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def set_status(callback: CallbackQuery, bot: Bot) -> None:
    if not admin_only(callback.from_user.id):
        await callback.answer("Недостаточно прав.", show_alert=True)
        return

    _, scope, index_str, request_id, new_status = callback.data.split(":", 4)
    await db.update_status(int(request_id), new_status)

    # Уведомление автору заявки о смене статуса 
    r = await db.get_request_by_id(int(request_id))
    if r and not admin_only(r["telegram_id"]):
        try:
            await bot.send_message(
                r["telegram_id"],
                "🔔 Статус Вашей заявки №{} изменён.\n"
                "Новый статус: {}\n"
                "Тип проблемы: {}\n"
                "Подразделение: {}".format(
                    r["id"], new_status, utils.esc(r["problem_type"]), utils.esc(r["department"])
                ),
            )
        except TelegramAPIError:
            pass

    text, keyboard = await render_card(scope, int(index_str))
    if text is None:
        await callback.message.edit_text(SCOPE_EMPTY_TEXT.get(scope, "Заявок нет."))
        await callback.answer(f"Статус изменён: {new_status}")
        return

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer(f"Статус изменён: {new_status}")


@router.message(F.text == kb.BTN_STATS)
async def statistics(message: Message, state: FSMContext) -> None:
    if not admin_only(message.from_user.id):
        return
    await state.clear()

    stats = await db.get_statistics()
    by_type_lines = "\n".join(f"  {utils.esc(k)}: {v}" for k, v in stats["by_type"].items())
    text = (
        "📊 Статистика заявок\n\n"
        f"Всего заявок: {stats['total']}\n"
        f"Новых: {stats['Новая']}\n"
        f"В работе: {stats['В работе']}\n"
        f"Выполненных: {stats['Выполнена']}\n"
        f"Отменённых: {stats['Отменена']}\n\n"
        "По типам проблем:\n" + (by_type_lines or "  нет данных")
    )
    await message.answer(text)
