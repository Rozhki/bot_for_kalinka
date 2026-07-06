from aiogram.fsm.state import State, StatesGroup


class RequestForm(StatesGroup):
    full_name = State()
    department = State()
    problem_type = State()
    description = State()
    priority = State()
