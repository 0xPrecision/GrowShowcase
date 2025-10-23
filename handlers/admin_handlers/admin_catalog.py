from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import EMOJI_MAP
from utils.admin_utils.catalog_utils import get_products_info
from database.crud import (
    get_product_by_id,
    get_products_page,
)
from keyboards.admin.catalog_keyboards import product_admin_keyboard
from utils.common_utils import delete_request_and_user_message

from .admin_access import admin_only

router = Router()


@router.callback_query(F.data == "admin_products")
@admin_only
async def admin_products_list(callback: CallbackQuery, state: FSMContext, t):
    """
    Displays the first page of products.
    """
    await delete_request_and_user_message(callback.message, state)
    page = 1
    text = t("spisok-tovarov")
    func = get_products_page(page)
    await get_products_info(callback, t, page, text, func, state)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_detail:"))
@admin_only
async def admin_product_detail(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Displays product details and an admin keyboard.
    """
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    if not product:
        await callback.answer(
            t("admin_catalog.messages.tovar-ne-najden"), show_alert=True
        )
        return
    product_name = product.name
    pr_price = product.price
    pr_descr = t(product.description) or "—"
    label = EMOJI_MAP.get(product.id, "📦")

    text = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
        product_name=f"{label} {product_name}",
        currency=t("currency") if product.id != 3 else "",
        price=pr_price if product.id != 3 else f"from ${pr_price}",
        description=pr_descr,
    )
    if product.photo:
        msg = await callback.message.answer_photo(
            photo=product.photo,
            caption=text,
            reply_markup=await product_admin_keyboard(product_id, t),
        )
        await callback.message.delete()
        await state.update_data(main_message_id=msg.message_id)
    else:
        msg = await callback.message.edit_text(
            text=text, reply_markup=await product_admin_keyboard(product_id, t)
        )
        await state.update_data(main_message_id=msg.message_id)
    await callback.answer()
