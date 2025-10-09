from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from utils.user_utils.user_orders_utils import get_order_details, show_orders_menu

router = Router()


@router.callback_query(F.data == "menu_orders")
async def show_history_orders_menu(
    callback: CallbackQuery, state: FSMContext, t
) -> None:
    """
    Handler for displaying the user's orders menu.
    """
    text = t("user_orders.misc.u-vas-poka-net")
    await show_orders_menu(callback, t, state, text)
    await callback.answer()


@router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery, t):
    order_id = int(callback.data.split("_")[2])
    details = await get_order_details(order_id, t)
    await callback.message.edit_text(details["text"], reply_markup=details["keyboard"])
