import csv
import io
import tempfile
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile

from database.models import Order, OrderItem, Product

from keyboards.admin.stats_kb import stats_actions
from .admin_access import admin_only

router = Router()


@router.callback_query(F.data == "admin_stats")
@admin_only
async def admin_stats_menu(callback: CallbackQuery, t):
    """
    Statistics main menu: summary and quick export of orders/products.
    """
    date_from = datetime.now() - timedelta(days=30)
    orders = await Order.filter(created_at__gte=date_from).all()
    orders_count = len(orders)
    total_sum = sum([float(o.total_price) for o in orders])
    top_products = {}
    for o in orders:
        items = await OrderItem.filter(order=o)
        for it in items:
            key = it.product_id
            top_products[key] = top_products.get(key, 0) + it.quantity
    top_products_sorted = sorted(top_products.items(), key=lambda x: -x[1])
    top_lines = []
    for idx, (prod_id, qty) in enumerate(top_products_sorted[:5], 1):
        prod = await Product.get_or_none(id=prod_id)
        if prod:
            top_lines.append(f"{idx}) {prod.name} — {qty} шт.")
    stats_text = (
        t("stats.header")
        + t("stats.orders_count").format(count=orders_count)
        + t("stats.total_sum").format(total=total_sum, currency=t("currency"))
        + t("stats.top_products")
        + ("\n".join(top_lines) if top_lines else t("stats.no_products"))
    )
    await callback.message.edit_text(stats_text, reply_markup=stats_actions(t))
    await callback.answer()


@router.callback_query(F.data == "admin_export_orders_csv")
@admin_only
async def export_orders_csv(callback: CallbackQuery, t, **_):
    """
    Exports orders for the last 30 days to CSV.
    """
    date_from = datetime.now() - timedelta(days=30)
    orders = await Order.filter(created_at__gte=date_from).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Date",
            "Customer",
            "Total",
            "Status",
            t("user_checkout_keyboards.buttons.sposob-oplaty"),
            t("user_checkout_keyboards.buttons.kommentarij"),
        ]
    )
    for o in orders:
        await o.fetch_related("user")
        writer.writerow(
            [
                o.id,
                o.created_at.strftime(t("date_format")),
                getattr(o.user, "full_name", "-"),
                f"{o.total_price:.2f}",
                o.status,
                o.payment_method,
                o.comment,
            ]
        )
    output.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmpfile:
        tmpfile.write(output.read().encode("utf-8"))
        tmpfile_path = tmpfile.name
    file_name = f"orders_{datetime.now().strftime(t("date_format"))}.csv"
    await callback.message.answer_document(
        FSInputFile(tmpfile_path, filename=file_name),
        caption="Orders export for 30 days (CSV)",
    )
    await callback.answer()
