from aiogram.filters.callback_data import CallbackData


class ReviewsCB(CallbackData, prefix="rev"):
    action: str   # open | next | prev
    index: int