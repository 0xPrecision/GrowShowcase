from aiogram.fsm.state import State, StatesGroup


class AddProductStates(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()
    waiting_stock = State()
    waiting_photo = State()
    waiting_category = State()
    confirming = State()


class EditProductStates(StatesGroup):
    choosing_field = State()
    editing_field = State()
    editing_category = State()
    confirming = State()


class ProductSearchStates(StatesGroup):
    waiting_query = State()
