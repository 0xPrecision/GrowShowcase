from typing import List, Optional, Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.common_utils import get_order_status_label
from database.models import Order


def show_orders_keyboard(orders: List[Order], t, **_) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for the user_kb's orders list.

    Each order line gets its own button to view details.
    At the bottom — a button to return to the main menu.

    :param orders: List of the user_kb's Order objects.
    :return: InlineKeyboardMarkup — inline keyboard.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=t("orders.list.item").format(
                    order_id=order.id,
                    status=t(
                        get_order_status_label(order.status, t)
                    ),  # тут возвращается локализованный текст со смайликом
                ),
                callback_data=f"order_details_{order.id}",
            )
        ]
        for order in orders
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("contact_me"),
                url="https://t.me/TGStoreLab",
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


def order_details_keyboard(
    *,
    t: Optional[Callable[[str], str]] = None,
    text_order: Optional[str] = None,
    text_menu: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для детального просмотра заказа.
    Вариант A: передай t (i18n), ключи возьмём внутри.
    Вариант B: передай готовые текстовые лейблы.

    Исключение, если не удалось получить тексты.
    """
    if t is not None:
        text_order = t("order_keyboards.buttons.k-spisku-zakazov")
        text_menu = t("order_keyboards.buttons.v-glavnoe-menyu")
    else:
        if not text_order or not text_menu:
            raise ValueError("Either provide t or both text_order and text_menu")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text_order, callback_data="menu_orders")],
            [InlineKeyboardButton(text=text_menu, callback_data="menu_main")],
        ]
    )


def order_confirm_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.oformit-zakaz"),
                    callback_data="confirm_order",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_cart_keyboards.buttons.v-katalog"),
                    callback_data="menu_offers",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("order_keyboards.buttons.redaktirovat-dannye"),
                    callback_data="edit_data",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="cancel_order",
                )
            ],
        ]
    )
