from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.user_kb.user_checkout_keyboards import payment_methods_keyboard
from states.user_states.order_states import OrderStates
from utils.common_utils import delete_request_and_user_message
from utils.user_utils.user_common_utils import send_step_and_cleanup
from utils.user_utils.user_orders_utils import show_order_summary


async def editing_name(message: Message, state: FSMContext, t):
    """
    Handles entering a new full name in edit mode.
    """
    name = message.text
    await state.update_data(client_name=name)
    await show_order_summary(message, state, t)


async def editing_comment(message: Message, state: FSMContext, t):
    """
    Handles entering a new comment in edit mode.
    Validates input and shows a summary.
    """
    comment = message.text
    await state.update_data(comment=comment)
    await show_order_summary(message, state, t)


async def editing_payment(callback: CallbackQuery, state: FSMContext, t, **_):
    """
    Handles selecting a new payment method in edit mode.
    Validates input and shows a summary.
    """
    METHOD_LABELS = {
        "stripe": t("user_checkout_keyboards.buttons.kartoj-onlajn"),
        "pay_crypto": t("user_checkout_keyboards.buttons.crypto"),
    }
    key = callback.data
    if key not in METHOD_LABELS:
        await callback.answer(
            t("user_checkout.messages.neizvestnyj-sposob-oplaty"), show_alert=True
        )
        return
    label = METHOD_LABELS[key]
    await state.update_data(payment_method=key, payment_label=label)
    await callback.message.delete()
    await show_order_summary(callback, state, t)


async def process_comment(
    *,
    state: FSMContext,
    t,
    raw_comment: str | None,
    send_obj,  # Message или CallbackQuery
):
    # нормализация комментария
    comment = (raw_comment or "").strip()
    if not comment or comment == "-":
        comment = "-"

    # подчистим следы
    if isinstance(send_obj, Message):
        await delete_request_and_user_message(send_obj, state)
    else:
        # CallbackQuery
        await delete_request_and_user_message(send_obj.message, state)

    # сохраняем
    await state.update_data(comment=comment)
    data = await state.get_data()

    text = t("user_checkout.misc.zapolnite-dannye-dlya-zakaza").format(
        full_name=data.get("client_name"),
        comment=data.get("comment"),
    )

    # отвечаем пользователю и идём к выбору способа оплаты
    await send_step_and_cleanup(
        message=send_obj if isinstance(send_obj, Message) else send_obj.message,
        text=text,
        state=state,
        reply_markup=payment_methods_keyboard(t),
    )
    await state.set_state(OrderStates.choosing_payment)

    # красиво закрываем callback, если это он
    if isinstance(send_obj, CallbackQuery):
        await send_obj.answer()
