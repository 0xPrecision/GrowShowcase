from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.admin_handlers.admin_access import admin_only
from keyboards.admin.catalog_keyboards import back_menu
from keyboards.admin.order_keyboards import show_orders_for_search
from states.admin_states.order_states import OrderSearchStates
from utils.admin_utils.order_utils import admin_show_order_summary
from utils.common_utils import delete_request_and_user_message
from database.models import Order, User

router = Router()


@router.callback_query(F.data == "admin_search_order")
@admin_only
async def start_search_order(callback: CallbackQuery, state: FSMContext, t, **_):
    """
    Starts the FSM for order search.
    """
    msg = await callback.message.edit_text(
        t("search_order.messages.vvedite-id-zakaza"), reply_markup=back_menu(t)
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(OrderSearchStates.waiting_query)
    await callback.answer()


@router.message(OrderSearchStates.waiting_query)
@admin_only
async def search_order_query(message: Message, state: FSMContext, t, **_):
    """
    Searches for an order by ID, name, or phone number.
    """
    await delete_request_and_user_message(message, state)
    query = message.text.strip()
    orders = []
    if query.isdigit():
        order = await Order.get_or_none(id=int(query))
        if order:
            orders = [order]
    if not orders:
        users = await User.filter(full_name__icontains=query).all()
        if users:
            user_ids = [u.id for u in users]
            orders = await Order.filter(user_id__in=user_ids).all()
    if not orders and query.replace("+", "").isdigit():
        users = await User.filter(phone__icontains=query).all()
        if users:
            user_ids = [u.id for u in users]
            orders = await Order.filter(user_id__in=user_ids).all()
    if not orders:
        await message.answer(
            t('search_product.messages.nichego-ne-najdeno-poprobujte"'),
            reply_markup=back_menu(t),
        )
        await state.clear()
        return
    if len(orders) == 1:
        order = orders[0]
        await admin_show_order_summary(message, state, order, order.id, t)
        await state.clear()
    else:
        msg = await message.answer(
            t("search_order.naydeno-zakazov").format(orders=len(orders)),
            reply_markup=show_orders_for_search(orders, t),
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.clear()
