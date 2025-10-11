from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_menu(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.katalog"),
                    callback_data="admin_products",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("help_keyboard.buttons.zakazy"), callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("admin_add_review"), callback_data="admin_add_review"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("admin_menu.buttons.vygruzit-statistiku"),
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("admin_menu.buttons.pomosch"), callback_data="admin_help"
                )
            ],
        ]
    )
