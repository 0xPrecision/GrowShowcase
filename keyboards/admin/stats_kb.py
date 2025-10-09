from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def stats_actions(t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("stats_kb.buttons.vygruzit-zakazy-csv"),
                    callback_data="admin_export_orders_csv",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.nazad"),
                    callback_data="/start_admin",
                )
            ],
        ]
    )
