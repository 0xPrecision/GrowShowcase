from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from constants import EMOJI_MAP
from utils.user_utils.common_utils import format_price, format_product_name

def show_products_keyboard(
    products: list, t, **_
) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for displaying products with pagination.

    :param products: List of products.
    :return: InlineKeyboardMarkup with products.
    """
    rows = [
        [
            InlineKeyboardButton(
                text=f"{EMOJI_MAP.get(product.id, "🗂️")} {format_product_name(product.name, 70)} — {t("currency")}{format_price(product.price)}",
                callback_data=f"product_{product.id}_offers",
            ),
        ]
        for product in products
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=t("contact_me"),
                url="https://t.me/TGStoreLab"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.nazad"),
                callback_data="menu_main"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def show_product_info_kb(
    product_id: int, product_name, source, t, **_
) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard for product details.

    :param product_id: Product ID.
    :param product_name: Product name.
    :param source: Source from which the product card was opened.
    :return: InlineKeyboardMarkup.
    """
    if source == "offers":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("user_catalog_keyboards.buttons.v-korzinu").format(product=product_name),
                        callback_data=f"addtocart_{product_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t("user_catalog_keyboards.buttons.korzina"),
                        callback_data="menu_cart",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t("catalog_keyboards.buttons.nazad"),
                        callback_data="menu_offers",
                    )
                ],
            ]
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("user_cart_keyboards.buttons.ubrat-iz-korziny").format(product=product_name),
                        callback_data=f"removefromcart_{product_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t("catalog_keyboards.buttons.nazad"),
                        callback_data="edit_cart",
                    )
                ],
            ]
        )

    return kb