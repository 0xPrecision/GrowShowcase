from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.common_utils import format_product_name


def cart_keyboard(
    products: list, t, **_
) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for the cart with navigation and a “Pay” button.
    :param products: List of (Cart, Product).
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{format_product_name(product.name)}",
                callback_data=f"product_{product.id}_cart",
            ),
            InlineKeyboardButton(
                text=t("user_cart_keyboards.buttons.ubrat-iz-korziny"),
                callback_data=f"removefromcart_{product.id}",
            ),
        ]
        for items, product in products
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("user_cart_keyboards.buttons.back_to_placement"),
                callback_data="back_to_confirm",
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("user_cart_keyboards.buttons.ochistit-korzinu"),
                callback_data="clear_cart",
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("user_cart_keyboards.buttons.v-katalog"),
                callback_data="menu_offers",
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                callback_data="menu_main",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def yes_or_no_kb(t):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("say_yes"),
                    callback_data="yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("say_no"),
                    callback_data="no",
                )
            ],
        ]
    )
