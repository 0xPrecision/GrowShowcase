from typing import Optional, Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def confirm_test_order_kb(t):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("start_test_order"),
                    callback_data="start_test",
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
                    text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                    callback_data="menu_main",
                )
            ],
        ]
    )


def after_cancellation_kb(
        *,
        t: Optional[Callable[[str], str]] = None,
        text_contact: Optional[str] = None,
        text_plans: Optional[str] = None,
        text_menu: Optional[str] = None
):
    if t is not None:
        text_contact = t("contact_me")
        text_plans = t("user_cart_keyboards.buttons.v-katalog")
        text_menu = t("order_keyboards.buttons.v-glavnoe-menyu")
    else:
        if not text_contact or not text_plans or not text_menu:
            raise ValueError("Either provide t or both text_order and text_menu")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text_contact,
                    url="https://t.me/TGStoreLab",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text_plans,
                    callback_data="menu_offers",
                )
            ],
            [
                InlineKeyboardButton(
                    text=text_menu,
                    callback_data="menu_main",
                )
            ],
        ]
    )


def use_username(t, username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("your_nickname_is").format(nickname=username),
                    callback_data="use",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("checkout_kb_fill_manually"),
                    callback_data="fill_manually",
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


def payment_methods_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.kartoj-onlajn"),
                    callback_data="stripe",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.crypto"),
                    callback_data="pay_crypto",
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
                    text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                    callback_data="menu_main",
                )
            ],
        ]
    )


def skip_comment_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("skip_comment"),
                    callback_data="skip_comment",
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
                    text=t("order_keyboards.buttons.v-glavnoe-menyu"),
                    callback_data="menu_main",
                )
            ],
        ]
    )


def checkout_edit_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("user_profile_keyboards.buttons.fio"),
                    callback_data="edit_name",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.kommentarij"),
                    callback_data="edit_comment",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.sposob-oplaty"),
                    callback_data="edit_payment",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.edit_cart"),
                    callback_data="edit_cart",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.nazad"),
                    callback_data="back_to_confirm",
                )
            ],
        ]
    )


def to_payment_kb(url, t):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("user_checkout.buttons.pay_now"), url=url)],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="cancel_order",
                )
            ],
        ]
    )
