from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import EMOJI_MAP
from database.crud import (
    create_order,
    get_cart,
    add_to_cart,
    clear_cart,
    get_product_by_id,
)
from states.user_states.order_states import OrderStates
from keyboards.user_kb.order_keyboards import order_details_keyboard
from keyboards.user_kb.user_checkout_keyboards import (
    payment_methods_keyboard,
    checkout_edit_keyboard,
    after_cancellation_kb,
    confirm_test_order_kb,
)
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from utils.common_utils import delete_request_and_user_message, format_price
from utils.user_utils.universal_handlers import universal_exit, universal_name_handler
from utils.user_utils.user_checkout_utils import (
    editing_name,
    editing_comment,
    editing_payment,
    notify_admin_about_new_order,
)
from utils.user_utils.user_common_utils import (
    start_manual_checkout,
    send_step_and_cleanup,
)
from utils.user_utils.user_orders_utils import show_order_summary

router = Router()


@router.callback_query(lambda c: c.data in ["menu_offers", "menu_main"])
async def checkout_exit_handler(callback: CallbackQuery, state: FSMContext, t):
    """
    Handler for exiting the checkout process via the “Catalog” or “Main Menu” buttons.
    Calls the universal exit function.
    """
    await universal_exit(callback, t, state)


@router.callback_query(F.data == "menu_cart")
async def show_demo_order(callback: CallbackQuery, t):
    product = await get_product_by_id(product_id=4)
    label = EMOJI_MAP.get(product.id, "📦")
    caption = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
        product_name=f"{label} {product.name}",
        price=format_price(product.price),
        currency=t("currency"),
        description=t(product.description) or t("product.card.no_description"),
    )
    kb = confirm_test_order_kb(t)

    if product.photo:
        await callback.message.delete()
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=product.photo,
            caption=caption,
            reply_markup=kb,
        )

    else:
        await callback.message.edit_text(text=caption, reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data == "start_test")
async def place_an_order_handler(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Starts the checkout process. Checks the cart.
    If a profile exists — suggests using it. Otherwise, starts a step-by-step input flow.
    """
    await delete_request_and_user_message(callback.message, state)
    user_id = callback.from_user.id
    username = callback.from_user.username
    cart_items = await get_cart(user_id)
    if not cart_items:
        await add_to_cart(user_id, product_id=4, quantity=1)

    await state.update_data(
        cart=[
            {"product_id": item.product_id, "qty": item.quantity} for item in cart_items
        ]
    )
    if username:
        await start_manual_checkout(callback, state, t, username)
        await state.set_state(OrderStates.waiting_for_ask)
    else:
        msg = await callback.message.answer(
            t("user_common_utils.messages.zapolnite-dannye-1-fio"),
            reply_markup=cart_back_menu(t),
        )
        await state.set_state(OrderStates.waiting_for_name)
        await state.update_data(main_message_id=msg.message_id)
    await callback.answer()


@router.callback_query(
    OrderStates.waiting_for_ask, F.data.in_({"use", "fill_manually"})
)
async def ask_nickname_handler(callback: CallbackQuery, state: FSMContext, t):
    await delete_request_and_user_message(callback.message, state)
    if callback.data == "use":
        nickname = f"Telegram @{callback.from_user.username or 'user'}"
        await state.update_data(name=nickname)
        text = t("universal_handlers.misc.zapolnite-dannye-fio").format(name=nickname)
        msg = await callback.message.answer(text, reply_markup=cart_back_menu(t))
        await state.set_state(OrderStates.waiting_for_comment)
    else:
        msg = await callback.message.answer(
            t("user_common_utils.messages.zapolnite-dannye-1-fio"),
            reply_markup=cart_back_menu(t),
        )
        await state.set_state(OrderStates.waiting_for_name)

    await state.update_data(main_message_id=msg.message_id)


@router.message(OrderStates.waiting_for_name)
async def name_handler_order(message: Message, state: FSMContext, t):
    """
    Handler for entering the name during checkout.
    Calls the generic name handler.
    """
    await universal_name_handler(message, state, t)


@router.message(OrderStates.editing_name)
async def edit_name_handler_order(message: Message, state: FSMContext, t):
    """
    Handler for editing the name during checkout.
    """
    await editing_name(message, state, t)


@router.message(OrderStates.waiting_for_comment)
async def order_comment_handler(message: Message, state: FSMContext, t):
    """
    Saves the user_kb's comment and proceeds to payment method selection.
    """
    await delete_request_and_user_message(message, state)
    await state.update_data(comment=message.text if message.text != "-" else "-")
    data = await state.get_data()
    text = t("user_checkout.misc.zapolnite-dannye-dlya-zakaza").format(
        full_name=data.get("name"), comment=data.get("comment")
    )
    await send_step_and_cleanup(
        message=message,
        text=text,
        state=state,
        reply_markup=payment_methods_keyboard(t),
    )
    await state.set_state(OrderStates.choosing_payment)


@router.message(OrderStates.editing_comment)
async def edit_comment_handler_order(message: Message, state: FSMContext, t):
    """
    Handler for editing the order comment.
    """
    await editing_comment(message, state, t)


@router.callback_query(OrderStates.choosing_payment)
async def choose_payment_method(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Handles the user_kb's selection of payment method.
    """
    await delete_request_and_user_message(callback.message, state)
    method = {
        "pay_card": t("user_checkout_keyboards.buttons.kartoj-onlajn"),
        "pay_crypto": t("user_checkout_keyboards.buttons.crypto"),
    }[callback.data]
    if not method:
        await callback.answer(
            t("user_checkout.messages.neizvestnyj-sposob-oplaty"), show_alert=True
        )
        return
    await state.update_data(payment_method=method)
    await show_order_summary(callback, state, t)
    await callback.answer()


@router.callback_query(OrderStates.editing_payment)
async def edit_payment_handler_order(callback: CallbackQuery, state: FSMContext, t):
    """
    Handler for editing the payment method of the order.
    """
    await editing_payment(callback, state, t)


@router.callback_query(OrderStates.confirm, F.data == "edit_data")
async def edit_data_handler(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Switches the user_kb into order data editing mode.
    Displays a keyboard to choose which field to edit.
    """
    await delete_request_and_user_message(callback.message, state)
    edit_msg = await callback.message.answer(
        t("user_checkout.messages.chto-vy-hotite-izmenit"),
        reply_markup=checkout_edit_keyboard(t),
    )
    await state.update_data(main_message_id=edit_msg.message_id)
    await callback.answer()


@router.callback_query(OrderStates.confirm, F.data == "edit_name")
async def edit_name_callback(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Start editing the full name.
    """
    await delete_request_and_user_message(callback.message, state)
    msg = await callback.message.answer(
        t("user_checkout.messages.vvedite-novye-fio"), reply_markup=cart_back_menu(t)
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OrderStates.editing_name)
    await callback.answer()


@router.callback_query(OrderStates.confirm, F.data == "edit_comment")
async def edit_comment_callback(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Start editing the comment.
    """
    await delete_request_and_user_message(callback.message, state)
    msg = await callback.message.answer(
        t("user_checkout.messages.vvedite-novyj-kommentarij-ili"),
        reply_markup=cart_back_menu(t),
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OrderStates.editing_comment)
    await callback.answer()


@router.callback_query(OrderStates.confirm, F.data == "edit_payment")
async def edit_payment_callback(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Start editing the payment method.
    """
    await delete_request_and_user_message(callback.message, state)
    msg = await callback.message.answer(
        t("user_checkout.messages.vyberite-sposob-oplaty"),
        reply_markup=payment_methods_keyboard(t),
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OrderStates.editing_payment)
    await callback.answer()


@router.callback_query(OrderStates.confirm, F.data == "back_to_confirm")
async def back_to_summary_callback(callback: CallbackQuery, state: FSMContext, t):
    """
    Return to the order summary.
    """
    await delete_request_and_user_message(callback.message, state)
    await show_order_summary(callback, state, t)
    await callback.answer()


@router.callback_query(OrderStates.confirm, F.data == "confirm_order")
async def order_confirm_handler(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Confirms checkout, adds the order to the database, clears the cart, and notifies the user_kb.
    """
    await delete_request_and_user_message(callback.message, state)
    user_id = callback.from_user.id
    data = await state.get_data()
    bot = callback.bot
    order = await create_order(
        user_id=user_id,
        name=data.get("name"),
        status="order.status.in_progress",
        payment_method=data.get("payment_method"),
        comment=data.get("comment"),
    )
    await notify_admin_about_new_order(bot, order, t)
    if not order:
        await callback.message.answer(
            t("user_checkout.messages.korzina-pusta"), reply_markup=cart_back_menu(t)
        )
        await state.clear()
        await callback.answer()
        return
    await callback.message.answer(
        t("user_checkout.messages.spasibo-vash-zakaz-oformlen"),
        reply_markup=order_details_keyboard(t),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Handles order cancellation.
    Clears the FSM state and notifies the user_kb.
    """
    user_id = callback.from_user.id
    await callback.message.edit_text(
        t("user_checkout.messages.oformlenie-zakaza-otmeneno"),
        reply_markup=after_cancellation_kb(t),
    )
    await clear_cart(user_id)
    await state.clear()
    await callback.answer()
