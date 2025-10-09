from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_menu_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("user_profile_keyboards.buttons.moi-dannye"),
                    callback_data="reviews",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("contact_me"),
                    url="https://t.me/TGStoreLab",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.nazad"),
                    callback_data="menu_main",
                )
            ],
        ]
    )

