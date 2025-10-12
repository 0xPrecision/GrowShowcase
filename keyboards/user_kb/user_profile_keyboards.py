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
    curr: int,
    total: int,
    t,
    contact_url: str | None = None,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по отзывам:
    - На первой странице: только "Вперёд", под ней "Контакт" и "Главное меню"
    - На промежуточных: "Назад" и "Вперёд"
    - На последней: только "Назад"
    """
    # Кнопки
    btn_prev = InlineKeyboardButton(
        text=t("catalog_keyboards.buttons.pred"),
        callback_data=ReviewsCB(action="prev", index=curr - 1).pack(),
    )
    btn_next = InlineKeyboardButton(
        text=t("catalog_keyboards.buttons.vpered"),
        callback_data=ReviewsCB(action="next", index=curr + 1).pack(),
    )

    btn_contact = (
        InlineKeyboardButton(text=t("contact_me"), url=contact_url)
        if contact_url
        else None
    )
    btn_home = InlineKeyboardButton(
        text=t("catalog_keyboards.buttons.vyjti-v-glavnoe"),
        callback_data="menu_main",
    )

    # Определяем, какие кнопки показывать
    keyboard: list[list[InlineKeyboardButton]] = []

    if curr == 0:
        # Первая страница
        if total > 1:
            keyboard.append([btn_next])

    elif curr == total - 1:
        # Последняя страница
        keyboard.append([btn_prev])

    else:
        # Промежуточные страницы
        keyboard.append([btn_prev, btn_next])

    if btn_contact:
        keyboard.append([btn_contact])
    keyboard.append([btn_home])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
