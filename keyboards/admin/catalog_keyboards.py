from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.crud import get_product_by_id
from utils.user_utils.common_utils import format_price


def back_menu(t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.vyjti-v-glavnoe"),
                    callback_data="/start_admin",
                )
            ]
        ]
    )


def admin_ask_new_product(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.dobavit-noviy-tovar"),
                    callback_data="admin_add_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.k-tovaram"),
                    callback_data="admin_products",
                )
            ],
        ]
    )


def admin_catalog_menu_keyboard(t, **_):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.tovary"),
                    callback_data="admin_products",
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


def create_or_cancel_product_kb(t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.sozdat"),
                    callback_data="admin_create_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="admin_products",
                )
            ],
        ]
    )


def ask_of_create_product(t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.dobavit-tovar"),
                    callback_data="admin_add_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="/start_admin",
                )
            ],
        ]
    )


def create_or_cancel_edit_product_kb(t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.sohranit"),
                    callback_data="edit_save",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="admin_products",
                )
            ],
        ]
    )


def confirm_deletion_product(product_id: int, t, **_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.da-skryt"),
                    callback_data=f"admin_delete_product_yes:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.net-otmena"),
                    callback_data="admin_products",
                )
            ],
        ]
    )


def products_list_keyboard(
    products: List[Tuple[int, str]], page: int, has_next: bool, has_prev: bool, t, **_
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=short_info, callback_data=f"admin_product_detail:{prod_id}"
            )
        ]
        for prod_id, short_info in products
    ]
    nav = []
    if has_prev:
        nav.append(
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.nazad"),
                callback_data=f"admin_products_page:{page - 1}",
            )
        )
    if has_next:
        nav.append(
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.vpered"),
                callback_data=f"admin_products_page:{page + 1}",
            )
        )
    if nav:
        buttons.append(nav)
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.poisk-tovara"),
                callback_data="admin_search_product",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.dobavit-tovar"),
                callback_data="admin_add_product",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.vyjti-v-glavnoe"),
                callback_data="/start_admin",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def show_products_for_search(products, t) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"#_id {p.id} | {p.name} | {format_price(p.price)} {t("currency")} | {p.status_label(t)}",
                callback_data=f"admin_product_detail:{p.id}",
            )
        ]
        for p in products
    ]

    keyboard.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.nazad"),
                callback_data="admin_products",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_search_keyboard(t, **_) -> InlineKeyboardMarkup:
    """
    Keyboard for returning to product search.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.povtorit-popytku"),
                    callback_data="admin_search_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.k-tovaram"),
                    callback_data="admin_products",
                )
            ],
        ]
    )


async def product_admin_keyboard(product_id: int, t, **_) -> InlineKeyboardMarkup:
    """
    Keyboard for editing and deleting/restoring a product.
    Покажи delete, если товар активен; restore — если в архиве.
    """
    rows = [
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.redaktirovat"),
                callback_data=f"admin_edit_product:{product_id}",
            )
        ]
    ]

    product = await get_product_by_id(product_id)
    is_active = product.is_active

    if is_active:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.udalit"),
                    callback_data=f"admin_delete_product:{product_id}",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.vosstanovit"),
                    callback_data=f"admin_restore_product:{product_id}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text=t("catalog_keyboards.buttons.k-tovaram"),
                callback_data="admin_products",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_edit_field_keyboard(product_id: int, t, **_) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting a product field to edit.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.nazvanie"),
                    callback_data=f"edit_field:name:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.opisanie"),
                    callback_data=f"edit_field:description:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.cena"),
                    callback_data=f"edit_field:price:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.foto"),
                    callback_data=f"edit_field:photo:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.podtverdit"),
                    callback_data=f"edit_field:confirm:{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("catalog_keyboards.buttons.otmena"),
                    callback_data="admin_products",
                )
            ],
        ]
    )