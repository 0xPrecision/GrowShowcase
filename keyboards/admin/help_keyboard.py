from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def help_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.katalog"),
                    callback_data="admin_catalog",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.zakazy"), callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.dobavit-tovar"),
                    callback_data="admin_add_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.glavnoe-menyu"),
                    callback_data="/start_admin",
                )
            ],
        ]
    )
