from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.admin.order_keyboards import status_keyboard
from database.crud import get_order_by_id
from database.models import Order

from utils.admin_utils.order_utils import admin_show_order_summary, show_orders
from utils.common_utils import get_order_status_label
from .admin_access import admin_only

router = Router()


@router.callback_query(F.data == "admin_orders")
@admin_only
async def admin_orders_list(callback: CallbackQuery, t):
    """
    Displays the first page of the orders list.
    """
    page = 1
    text = t("admin_orders.misc.b-spisok-zakazov-b-vyberi")
    await show_orders(callback, t, page, text)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders_page:"))
@admin_only
async def admin_orders_page(callback: CallbackQuery, t):
    """
    Paginates through the orders list.
    """
    page = int(callback.data.split(":")[1])
    text = t("admin_orders.misc.b-spisok-zakazov-b-str").format(page=page)
    await show_orders(callback, t, page, text)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_detail:"))
@admin_only
async def admin_order_detail(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Displays details of a single order.
    """
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    order = await get_order_by_id(order_id)
    if not order:
        await callback.answer(
            t("admin_orders.messages.zakaz-ne-najden"), show_alert=True
        )
        return
    await admin_show_order_summary(callback, state, order, order_id, t)
    await callback.answer()


@router.callback_query(F.data == "change_status")
@admin_only
async def change_order_status_menu(callback: CallbackQuery, state: FSMContext, t, **_):
    """
    Displays a keyboard with order statuses.
    :param callback: Admin's CallbackQuery.
    """
    message = callback.message
    data = await state.get_data()
    order_id = data.get("order_id")
    order = await get_order_by_id(order_id)
    if not order:
        await callback.answer(
            t("admin_orders.messages.zakaz-ne-najden"), show_alert=True
        )
        return
    await message.edit_reply_markup(
        reply_markup=status_keyboard(order.id, t, order.status)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_set_status:"))
@admin_only
async def set_order_status(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Saves the selected order status, notifies the customer, and returns to the order details.
    """
    _, order_id, new_status = callback.data.split(":")
    order_id = int(order_id)
    order = await Order.get_or_none(id=order_id).prefetch_related("user")
    if not order:
        await callback.answer(
            t("admin_orders.messages.zakaz-ne-najden"), show_alert=True
        )
        return
    status_label = get_order_status_label(new_status, t)
    await order.update_from_dict({"status": status_label}).save()
    try:
        text = t("admin_orders.misc.soobschenie-dlya-polzovatelya-vash").format(
            id=order.id, status_label=status_label
        )
        await callback.bot.send_message(chat_id=order.user.id, text=text)
    except Exception as e:
        print(f"[OrderNotify] Не удалось отправить клиенту: {e}")
    await admin_show_order_summary(callback, state, order, order_id, t)
    await callback.answer(t("admin_orders.messages.status-zakaza-izmenen-klient"))
