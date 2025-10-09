from aiogram.fsm.state import State, StatesGroup


class OrderSearchStates(StatesGroup):
    waiting_query = State()
