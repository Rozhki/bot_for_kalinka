from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
import utils
from config import ADMIN_ID
from states import RequestForm

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id == ADMIN_ID


def main_menu_for(telegram_id: int):
    return kb.admin_main_menu() if is_admin(telegram_id) else kb.user_main_menu()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Здравствуйте! Это бот для регистрации заявок.\n\n"
        "Выберите действие в меню ниже.",
        reply_markup=main_menu_for(message.from_user.id),
    )


@router.message(F.text == kb.BTN_HELP)
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Этот бот предназначен для регистрации обращений в ИТ-службу.\n\n"
        "• «Создать заявку» - создать новое обращение по неисправности техники, "
        "ПО.\n"
        "• «Мои заявки» - посмотреть список и статус Ваших обращений.\n\n"
        "После создания заявки Вы получите её номер, по которому "
        "специалист будет отслеживать выполнение."
    )


@router.message(F.text == kb.BTN_NEW_REQUEST)
async def start_request(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RequestForm.full_name)
    await message.answer("Введите ваше ФИО:")


@router.message(RequestForm.full_name, ~F.text.in_(kb.RESERVED_TEXTS))
async def process_full_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, введите ФИО текстом.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(RequestForm.department)
    await message.answer("Укажите подразделение или место возникновения проблемы:")


@router.message(RequestForm.department, ~F.text.in_(kb.RESERVED_TEXTS))
async def process_department(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, укажите подразделение текстом.")
        return
    await state.update_data(department=message.text.strip())
    await state.set_state(RequestForm.problem_type)
    await message.answer("Выберите тип проблемы:", reply_markup=kb.problem_type_keyboard())


@router.callback_query(RequestForm.problem_type, F.data.startswith("ptype:"))
async def process_problem_type(callback: CallbackQuery, state: FSMContext) -> None:
    index = int(callback.data.split(":")[1])
    problem_type = kb.PROBLEM_TYPES[index]
    await state.update_data(problem_type=problem_type)
    await state.set_state(RequestForm.description)
    await callback.message.edit_text(f"Тип проблемы: {problem_type}")
    await callback.message.answer("Опишите проблему подробнее:")
    await callback.answer()


@router.message(RequestForm.description, ~F.text.in_(kb.RESERVED_TEXTS))
async def process_description(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, опишите проблему текстом.")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(RequestForm.priority)
    await message.answer("Выберите срочность заявки:", reply_markup=kb.priority_keyboard())


@router.callback_query(RequestForm.priority, F.data.startswith("priority:"))
async def process_priority(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    priority = callback.data.split(":")[1]
    data = await state.update_data(priority=priority)
    await state.clear()

    request_id = await db.create_request(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data["full_name"],
        department=data["department"],
        problem_type=data["problem_type"],
        description=data["description"],
        priority=priority,
    )

    await callback.message.edit_text(f"Срочность: {priority}")
    await callback.message.answer(
        f"✅ Ваша заявка №{request_id} зарегистрирована.\nСтатус: новая.",
        reply_markup=main_menu_for(callback.from_user.id),
    )
    await callback.answer()

    if not is_admin(callback.from_user.id):
        author_link = utils.user_link(
            callback.from_user.id, callback.from_user.username, data["full_name"]
        )
        await bot.send_message(
            ADMIN_ID,
            "🆕 Создана новая ИТ-заявка №{}\n"
            "Подразделение: {}\n"
            "Тип проблемы: {}\n"
            "Срочность: {}\n"
            "Автор: {}".format(
                request_id,
                utils.esc(data["department"]),
                utils.esc(data["problem_type"]),
                utils.esc(priority),
                author_link,
            ),
        )


@router.message(F.text == kb.BTN_MY_REQUESTS)
async def my_requests(message: Message, state: FSMContext) -> None:
    await state.clear()
    requests = await db.get_user_requests(message.from_user.id)
    if not requests:
        await message.answer("У Вас пока нет заявок.")
        return

    lines = []
    for r in requests:
        lines.append(
            f"№{r['id']} - {r['problem_type']}\n"
            f"Статус: {r['status']}\n"
            f"Срочность: {r['priority']}\n"
            f"Создана: {r['created_at']}"
        )
    await message.answer("\n\n".join(lines))
