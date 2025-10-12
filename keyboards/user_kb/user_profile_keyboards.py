from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.user_utils.user_profile_utils import ReviewsCB


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


def reviews_kb(
    curr: int, total: int, contact_url: str | None = None
) -> InlineKeyboardMarkup:
    prev_idx = (curr - 1) % total
    next_idx = (curr + 1) % total

    prev_btn = InlineKeyboardButton(
        text="catalog_keyboards.buttons.pred",
        callback_data=ReviewsCB(action="prev", index=prev_idx).pack(),
    )
    next_btn = InlineKeyboardButton(
        text="catalog_keyboards.buttons.vpered",
        callback_data=ReviewsCB(action="next", index=next_idx).pack(),
    )
    row = [prev_btn, next_btn]

    if contact_url:
        row.append(InlineKeyboardButton(text="contact_me", url=contact_url))

    return InlineKeyboardMarkup(inline_keyboard=[row])
