from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.user_handlers.user_catalog import show_products
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from keyboards.user_kb.user_main_menu import main_menu
from states.user_states.order_states import OrderStates
from utils.common_utils import delete_request_and_user_message
from utils.user_utils.user_common_utils import send_step_and_cleanup

router = Router()


async def universal_name_handler(message: Message, state: FSMContext, t) -> None:
    """
    Full name handler for checkout.
    Messages are always cleared.
    """
    await delete_request_and_user_message(message, state)
    name = message.text
    await state.update_data(name=name)
    text = t("universal_handlers.misc.zapolnite-dannye-fio").format(name=name)
    await send_step_and_cleanup(message, text, state, reply_markup=cart_back_menu(t))
    await state.set_state(OrderStates.waiting_for_comment)


async def universal_exit(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Universal function to exit the current scenario (checkout, etc.).
    Clears previous messages and resets the FSM state.

    :param callback: User's CallbackQuery object.
    :param state: FSM context.
    """
    await delete_request_and_user_message(callback.message, state)
    if callback.data == "menu_offers":
        await show_products(callback, t)
    elif callback.data == "menu_main":
        await callback.message.answer(
            t("universal_handlers.messages.vy-vernulis-v-glavnoe"),
            reply_markup=main_menu(t),
        )
    await state.clear()
    await callback.answer()
