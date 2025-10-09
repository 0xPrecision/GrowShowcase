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

def after_cancellation_kb(t):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("contact_me"),
                    url="https://t.me/TGStoreLab",
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
            ]
        ]
    )


def payment_methods_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("user_checkout_keyboards.buttons.kartoj-onlajn"),
                    callback_data="pay_card",
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


