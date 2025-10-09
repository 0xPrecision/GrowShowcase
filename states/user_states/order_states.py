from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    waiting_for_cancel = State()
    waiting_for_ask = State()
    waiting_for_name = State()
    waiting_for_comment = State()
    choosing_payment = State()
    confirm = State()
    editing_field = State()
    editing_name = State()
    editing_payment = State()
    editing_comment = State()
