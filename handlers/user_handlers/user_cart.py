import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config_data.bot_instance import bot
from database.crud import (
    get_all_products, get_cart, clear_cart
)
from keyboards.user_kb.user_cart_keyboards import yes_or_no_kb
from keyboards.user_kb.user_checkout_keyboards import after_cancellation_kb
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from keyboards.user_kb.user_main_menu import main_menu
from states.user_states.order_states import OrderStates
from utils.common_utils import delete_request_and_user_message
from utils.user_utils.user_cart_utils import build_cart_view

router = Router()

@router.callback_query(F.data == "edit_cart")
async def show_cart(callback: CallbackQuery, state: FSMContext, t, **_) -> None:
    """
    Displays the user's cart.
    """
    await delete_request_and_user_message(callback.message, state)
    user_id = callback.from_user.id
    cart_items = await get_cart(user_id)
    if cart_items:
        text, keyboard = await build_cart_view(cart_items, t)
        await callback.bot.send_message(
            user_id, text, reply_markup=keyboard or main_menu(t)
        )
    else:
        await bot.send_message(
            user_id,
            t("user_cart.messages.vasha-korzina-pusta"),
            reply_markup=cart_back_menu(t),
        )


@router.callback_query(F.data.startswith("addtocart_"))
async def add_to_cart_handler(callback: CallbackQuery, t, **_) -> None:
    """
    Handler for the 'Add to cart' button: adds a product to the user_kb's cart.

    :param callback: User's CallbackQuery.
    :return: None
    """
    user_id = callback.from_user.id
    admin_id = -1003030319198
    username = callback.from_user.username
    product_id = int(callback.data.split("_")[1])
    products = await get_all_products()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        await callback.answer(t("user_cart.messages.tovar-ne-najden"), show_alert=True)
        return
    await callback.bot.send_message(
        chat_id=admin_id,
        text=t("user_cart.messages.tovar-dobavlen-v-korzinu").format(
            package=product.name, username=username)
    )
    sent_message = await bot.send_message(user_id, t("user_package_confirmed"))
    await asyncio.sleep(3)
    await bot.delete_message(user_id, sent_message.message_id)


@router.callback_query((F.data == "clear_cart") | (F.data.startswith("removefromcart_")))
async def ask_before_cancellation(callback: CallbackQuery, state: FSMContext, t):
    try:
        await callback.message.edit_text(t("action_will_cancel_order"), reply_markup=yes_or_no_kb(t))
    except TelegramBadRequest:
        await delete_request_and_user_message(callback.message, state)
        msg = await callback.message.answer(t("action_will_cancel_order"), reply_markup=yes_or_no_kb(t))
        await state.update_data(main_message_id=msg.message_id)
        await callback.answer()

    cur_state = await state.get_state()
    await state.update_data(cur_state=cur_state)
    await state.set_state(OrderStates.waiting_for_cancel)


@router.callback_query(OrderStates.waiting_for_cancel, F.data.in_({"yes", "no"}))
async def cancel_or_not(callback: CallbackQuery, state: FSMContext, t):
    if callback.data == "yes":
        user_id = callback.from_user.id
        await clear_cart(user_id)
        await delete_request_and_user_message(callback.message, state)
        await bot.send_message(
            user_id,
            t("user_cart.messages.vasha-korzina-pusta"),
            reply_markup=after_cancellation_kb(t),
        )
    else:
        data = await state.get_data()
        await state.set_state(data.get("cur_state"))
        await show_cart(callback, state, t)
