from aiogram import F, Router
from aiogram.types import CallbackQuery

from constants import EMOJI_MAP
from keyboards.user_kb.user_catalog_keyboards import show_product_info_kb, show_products_keyboard
from utils.user_utils.common_utils import format_price
from database.crud import get_all_products
from database.models import Product

router = Router()

async def show_products(callback: CallbackQuery, t, **_) -> None:
    """
    Displays the list of products.
    """
    products = await get_all_products()
    await callback.message.answer(
        t("user_catalog.messages.vyberite-kategoriyu"),
        reply_markup=show_products_keyboard(products[:3], t),
    )


@router.callback_query(F.data.startswith("product_"))
async def show_product_info(callback: CallbackQuery, t, **_):
    """
    Generic handler for displaying product details,
    distinguishes the source (catalog/cart) by callback_data.
    """
    try:
        parts = callback.data.split("_")
        product_id = int(parts[1])
        source = parts[2]
    except (IndexError, ValueError):
        await callback.answer(
            t("user_catalog.messages.nekorrektnyj-tovar"), show_alert=True
        )
        return

    product = await Product.get_or_none(id=product_id)

    if not product:
        await callback.answer(
            t("admin_catalog.messages.tovar-ne-najden"), show_alert=True
        )
        return
    label = EMOJI_MAP.get(product.id, "📦")

    caption = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
        product_name=f"{label} {product.name}",
        price=format_price(product.price),
        currency=t("currency"),
        description=t(product.description) or t("product.card.no_description"),
    )
    kb = show_product_info_kb(product.id, product.name, source, t)

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
