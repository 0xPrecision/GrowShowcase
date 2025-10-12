from decimal import Decimal
from typing import List, Tuple

from aiogram.types import InlineKeyboardMarkup

from database.models import Cart, Product
from keyboards.user_kb.user_cart_keyboards import cart_keyboard
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from utils.common_utils import format_price


async def build_cart_view(
    cart_items: List[Cart], t, **_
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Builds text and a keyboard for displaying the user_kb's cart with pagination.
    Shows the full cart in the text, but only products for the current page in inline buttons.

    :param cart_items: List of the user_kb's Cart objects.
    :return: Tuple (message text, inline keyboard).
    """
    if cart_items:
        product_ids = [item.product_id for item in cart_items]
        products = await Product.filter(id__in=product_ids).all()
        products_dict = {p.id: p for p in products}
        cart_pairs = []
        total = 0
        for item in cart_items:
            product = products_dict.get(item.product_id)
            if product:
                amount = item.quantity * Decimal(product.price)
                total += amount
                cart_pairs.append((item, product))
        text = t("user_cart_utils.misc.b-vasha-korzina-b")
        for item, product in cart_pairs:
            product_price = product.price * item.quantity
            text += t("cart.item_line").format(
                name=product.name,
                qty=item.quantity,
                unit_price=format_price(product.price),
                total=format_price(product_price),
                currency=t("currency"),
            )
        text += t("cart.total").format(
            total=format_price(total), currency=t("currency")
        )

        keyboard = cart_keyboard(cart_pairs, t)
        return text, keyboard
    else:
        return t("user_cart.messages.vasha-korzina-pusta"), cart_back_menu(t)
