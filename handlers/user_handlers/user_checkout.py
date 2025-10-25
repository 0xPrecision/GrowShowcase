import logging
import os

from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv

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
    get_order_items,
)
from payments.cryptomus_gateway import CryptomusGateway
from payments.stripe_gateway import StripeGateway
from states.user_states.order_states import OrderStates
from keyboards.user_kb.user_checkout_keyboards import (
    payment_methods_keyboard,
    checkout_edit_keyboard,
    after_cancellation_kb,
    confirm_test_order_kb,
    skip_comment_keyboard,
    to_payment_kb,
)
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from utils.common_utils import delete_request_and_user_message
from utils.user_utils.universal_handlers import universal_exit, universal_name_handler
from utils.user_utils.user_checkout_utils import (
    editing_name,
    editing_comment,
    editing_payment,
    process_comment,
)
from utils.user_utils.user_common_utils import start_manual_checkout
from utils.user_utils.user_orders_utils import show_order_summary

router = Router()
load_dotenv()
REDIS_URL=os.getenv("REDIS_URL")
storage = RedisStorage.from_url(REDIS_URL)
log = logging.getLogger("web")


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
    if not product:
        await callback.answer(
            t("admin_catalog.messages.tovar-ne-najden"), show_alert=True
        )
        return
    label = EMOJI_MAP.get(product.id, "📦")
    caption = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
        product_name=f"{label} {product.name}",
        price=product.price,
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
        await state.update_data(client_name=nickname)
        text = t("universal_handlers.misc.zapolnite-dannye-fio").format(name=nickname)
        msg = await callback.message.answer(text, reply_markup=skip_comment_keyboard(t))
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


@router.callback_query(OrderStates.waiting_for_comment, F.data == "skip_comment")
async def order_comment_skip(callback: CallbackQuery, state: FSMContext, t):
    await process_comment(
        state=state,
        t=t,
        raw_comment="-",
        send_obj=callback,
    )


@router.message(OrderStates.waiting_for_comment)
async def order_comment_message(message: Message, state: FSMContext, t):
    await process_comment(
        state=state,
        t=t,
        raw_comment=message.text,
        send_obj=message,
    )


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
    Финальный шаг чекаута:
      - фиксируем заказ (pending) из корзины
      - создаём платёжную сессию выбранным провайдером
      - отправляем пользователю ссылку на оплату
    Сообщения админу/клиенту после оплаты — из вебхука.
    """
    await delete_request_and_user_message(callback.message, state)

    user_id = callback.from_user.id
    data = await state.get_data()

    payment_method = (data.get("payment_method") or "").lower()
    client_name = data.get("client_name")
    comment = data.get("comment") or "-"
    currency = (data.get("currency") or "USD").upper()
    locale = data.get("locale")  # 'ru' | 'en' | 'auto'

    # 1) Создаём заказ из корзины (pending) и очищаем корзину
    order = await create_order(
        user_id=user_id,
        client_name=client_name,
        payment_method=payment_method,
        comment=comment,
        currency=currency,
    )

    items_payload = []
    if order:
        order_items = await get_order_items(order)
        items_payload = [
            {
                "title": it.title or "Item",
                "unit_amount_cents": int(it.unit_amount_cents),
                "quantity": int(it.quantity),
            }
            for it in order_items
            if int(it.unit_amount_cents) > 0 and int(it.quantity) > 0
        ]

    if not order or not items_payload:
        # если заказ уже создан, подчистим хвосты
        if order:
            try:
                await order.delete()  # или: order.status = "failed"; await order.save()
            except Exception:
                pass
        msg = await callback.message.answer(
            t("user_checkout.messages.korzina-pusta"),
            reply_markup=cart_back_menu(t),
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.clear()
        await callback.answer()
        return

    # 3) Роутинг по способу оплаты
    try:
        if payment_method == "stripe":
            gw = StripeGateway()
            res = gw.create_checkout(
                order_id=order.order_uid,
                currency=order.currency,
                items=items_payload,  # детальный чек
                locale=locale,
                metadata={
                    "cart_hash": order.meta.get("cart_hash") if order.meta else "",
                    "source": "telegram",
                },
            )
            # сохраняем айдишники Stripe для сверок и последующих вебхуков
            order.stripe_session_id = res.get("session_id") or order.stripe_session_id
            order.stripe_payment_intent = (
                res.get("payment_intent") or order.stripe_payment_intent
            )
            order.stripe_customer = res.get("customer") or order.stripe_customer
            await order.save()
            pay_url = res["url"]
            msg = await callback.message.answer(
                t("stripe_payment_message"),
                reply_markup=to_payment_kb(pay_url, t),
            )
            await storage.redis.setex(f"paymsg:{order.order_uid}", 86400, msg.message_id)
            await state.update_data(main_message_id=msg.message_id)

        elif payment_method == "pay_crypto":
            cg = CryptomusGateway()
            cp = await cg.create_invoice(
                amount="1.00",
                currency=order.currency,  # "USD"
                order_id=order.order_uid,
                title=f"{order.name or "Order"}",
                url_callback=f"{os.getenv('TELEGRAM_WEBHOOK_URL')}/webhook/cryptomus",
            )

            pay_url = cp.get("url") or cp.get("result", {}).get("url")
            invoice_uuid = (
                cp.get("uuid")
                or cp.get("payment_id")
                or cp.get("result", {}).get("uuid")
            )

            if not pay_url or not invoice_uuid:
                log.warning("CM invoice create failed: %s", cp)
                await callback.message.answer(
                    t("user_checkout.messages.oshibka-pri-sozdanii-platezha"),
                    reply_markup=cart_back_menu(t),
                )
                await callback.answer()
                return

            order.provider = "cryptomus"
            order.txid = str(invoice_uuid)
            await order.save()

            msg = await callback.message.answer(
                t("user_checkout.messages.perenapravlyaem-na-oplatu_stripe"),
                reply_markup=to_payment_kb(pay_url, t),
            )
            await storage.redis.setex(f"paymsg:{order.order_uid}", 86400, msg.message_id)
            await state.update_data(main_message_id=msg.message_id)
        else:
            # неизвестный способ оплаты
            msg = await callback.message.answer(
                t("user_checkout.messages.neizvestnyj-sposob-oplaty"),
                reply_markup=cart_back_menu(t),
            )
            await state.update_data(main_message_id=msg.message_id)
            await state.clear()
            await callback.answer()
            return

    except Exception as e:
        # не удалось создать платёжную сессию
        log.exception("CM create_invoice error: %s", e)
        msg = await callback.message.answer(
            t("user_checkout.messages.oshibka-pri-sozdanii-platezha"),
            reply_markup=cart_back_menu(t),
        )
        await state.update_data(main_message_id=msg.message_id)
        await callback.answer()
        return

    await state.update_data(order_uid=order.order_uid, awaiting_payment=True)
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
        reply_markup=after_cancellation_kb(t=t),
    )
    await clear_cart(user_id)
    await state.clear()
    await callback.answer()
