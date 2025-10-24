from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.models import Order
from keyboards.user_kb.order_keyboards import order_details_keyboard
from keyboards.user_kb.user_checkout_keyboards import after_cancellation_kb
from keyboards.user_kb.user_main_menu import main_menu
from utils.common_utils import delete_request_and_user_message


router = Router(name="start")


@router.message(CommandStart())
async def start_cmd(message: Message, command: CommandObject, t, state: FSMContext):
    """
    /start с поддержкой deep-link (?start=payload).
    Если payload есть — обрабатываем кейс (например, возврат из Stripe).
    Если payload пуст — показываем главное меню.
    """
    payload = (command.args or "").strip()[
        :64
    ]  # сюда прилетит твой order_uid (или токен)

    if payload:
        await delete_request_and_user_message(message, state)

        order = await Order.get_or_none(order_uid=payload)
        if not order:
            msg = await message.answer(
                t("user_common.messages.b-dobro-pozhalovat-v-magazin-b"),
                reply_markup=main_menu(t),
            )
            await state.update_data(main_message_id=msg.message_id)

        await order.fetch_related("user")
        if order and order.user.id == message.from_user.id:
            if order.status == "paid" and not order.notified_paid:
                amount_str = f"{order.total_price} {order.currency}"
                msg = await message.answer(
                    t("user_checkout.messages.spasibo-vash-zakaz-oformlen").format(
                        order_id=order.order_uid, amount=amount_str
                    ),
                    reply_markup=order_details_keyboard(t=t),
                )
                order.notified_paid = True
                await order.save()
                await state.update_data(main_message_id=msg.message_id)

            elif (
                order.status in ("cancelled", "failed", "expired")
                and not order.notified_cancel
            ):
                msg = await message.answer(
                    t("user_checkout.messages.oformlenie-zakaza-otmeneno"),
                    reply_markup=after_cancellation_kb(t=t),
                )
                order.notified_cancel = True
                await order.save()
                await state.update_data(main_message_id=msg.message_id)
            else:
                msg = await message.answer(
                    t("user_common.messages.b-dobro-pozhalovat-v-magazin-b"),
                    reply_markup=main_menu(t),
                )
                await state.update_data(main_message_id=msg.message_id)

        return

    await state.clear()
    await message.answer(
        t("user_common.messages.b-dobro-pozhalovat-v-magazin-b"),
        reply_markup=main_menu(t),
    )
