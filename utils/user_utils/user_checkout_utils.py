from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from utils.common_utils import format_price
from utils.user_utils.user_orders_utils import show_order_summary


async def editing_name(message: Message, state: FSMContext, t):
    """
    Handles entering a new full name in edit mode.
    """
    name = message.text
    await state.update_data(name=name)
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
    await callback.message.delete()
    await show_order_summary(callback, state, t)


async def notify_admin_about_new_order(bot: Bot, order, t):
    """
    Sends an admin notification about a new order.
    """
    text = t("user_checkout_utils.misc.soobschenie-dlya-administratora").format(
        id=order.id,
        full_name=order.name,
        total=format_price(order.total_price),
        currency=t("currency"),
        comment=order.comment,
    )
    admin_id = -1003030319198
    try:
        await bot.send_message(chat_id=admin_id, text=text)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")
