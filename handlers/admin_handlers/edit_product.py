from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import EMOJI_MAP
from keyboards.admin.catalog_keyboards import (
    admin_catalog_menu_keyboard,
    create_or_cancel_edit_product_kb,
    product_edit_field_keyboard,
)
from database.crud import get_product_by_id, update_product

from states.admin_states.product_states import EditProductStates
from utils.common_utils import delete_request_and_user_message, format_price
from .admin_access import admin_only

router = Router()


@router.callback_query(F.data.startswith("admin_edit_product:"))
@admin_only
async def edit_product_start(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Displays an inline keyboard to choose the field to edit.
    """
    await delete_request_and_user_message(callback.message, state)
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    await state.update_data(edit_product_id=product_id, edit_fields={})
    await show_edit_product_summary(callback.message, product, state, t)
    msg = await callback.message.answer(
        t("edit_product.messages.chto-hotite-izmenit"),
        reply_markup=product_edit_field_keyboard(product_id, t),
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(EditProductStates.choosing_field)
    await callback.answer()


@router.callback_query(
    EditProductStates.choosing_field, F.data.startswith("edit_field:")
)
@admin_only
async def choose_edit_field(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Starts editing the selected field.
    """
    await delete_request_and_user_message(callback.message, state)
    _, field, product_id = callback.data.split(":")
    await state.update_data(editing_field=field)
    if field == "photo":
        msg = await callback.message.answer(
            t("edit_product.messages.otpravte-novoe-foto-tovara")
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.set_state(EditProductStates.editing_field)
    elif field == "confirm":
        data = await state.get_data()
        product_id = data.get("edit_product_id")
        product = await get_product_by_id(product_id)
        edit_fields = data.get("edit_fields", {})
        await show_edit_product_summary(
            callback.message, product, state, t, edit_fields
        )
        msg = await callback.message.answer(
            t("edit_product.messages.podtverdit-izmeneniya"),
            reply_markup=create_or_cancel_edit_product_kb(t),
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.set_state(EditProductStates.confirming)
    else:
        field_labels = {
            "name": t("product.fields.name"),
            "price": t("product.fields.price"),
            "description": t("product.fields.description"),
        }

        msg = await callback.message.answer(
            t("product.prompt").format(field=field_labels[field])
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.set_state(EditProductStates.editing_field)
    await callback.answer()


@router.message(EditProductStates.editing_field)
@admin_only
async def process_edit_field(message: Message, t, state: FSMContext, **_):
    """
    Processes the new value of the selected field.
    """
    await delete_request_and_user_message(message, state)
    data = await state.get_data()
    field = data.get("editing_field")
    edit_fields = data.get("edit_fields", {})
    if field == "name":
        edit_fields["name"] = message.text.strip()
    elif field == "price":
        try:
            price = float(message.text.replace(",", ".").strip())
            if price <= 0:
                raise ValueError
            edit_fields["price"] = price
        except ValueError:
            msg = await message.answer(
                t("edit_product.messages.vvedite-korrektnuyu-cenu")
            )
            await state.update_data(main_message_id=msg.message_id)
            return
    elif field == "description":
        edit_fields["description"] = message.text.strip()
    elif field == "photo" and message.photo:
        edit_fields["photo"] = message.photo[-1].file_id
    else:
        msg = await message.answer(t("edit_product.messages.povtorite-vvod"))
        await state.update_data(main_message_id=msg.message_id)
        return
    await state.update_data(edit_fields=edit_fields)
    product_id = data.get("edit_product_id")
    product = await get_product_by_id(product_id)
    await show_edit_product_summary(message, product, state, t, edit_fields)
    msg = await message.answer(
        t("edit_product.messages.chto-hotite-izmenit-dalshe"),
        reply_markup=product_edit_field_keyboard(product_id, t),
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(EditProductStates.choosing_field)


@router.callback_query(EditProductStates.confirming, F.data == "edit_save")
@admin_only
async def save_product_edits(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Saves the changes to the product.
    """
    await delete_request_and_user_message(callback.message, state)
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    edit_fields = data.get("edit_fields", {})
    if not edit_fields:
        await callback.answer(
            t("edit_product.messages.net-izmenenij-dlya-sohraneniya"), show_alert=True
        )
        return
    await update_product(product_id, **edit_fields)
    msg = await callback.message.answer(
        t("edit_product.messages.izmeneniya-uspeshno-sohraneny"),
        reply_markup=admin_catalog_menu_keyboard(t),
    )
    await delete_summary(callback.message, state)
    await state.update_data(main_message_id=msg.message_id)
    await state.clear()
    await callback.answer()


async def show_edit_product_summary(
    message_or_callback, product, state, t, edit_fields: dict = None
):
    """
    Sends the product summary (including changes) with a photo (if any).
    """
    await delete_summary(message_or_callback, state)
    data = {
        "name": product.name,
        "price": product.price,
        "description": t(product.description),
        "photo": product.photo,
    }
    if edit_fields:
        data.update(edit_fields)
    label = EMOJI_MAP.get(product.id, "📦")

    text = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
        product_name=f"{label} {data["name"]}",
        price=format_price(data["price"]),
        currency=t("currency"),
        description=t(data["description"]) or "—",
    )
    if data.get("photo"):
        try:
            msg = await message_or_callback.bot.send_photo(
                chat_id=message_or_callback.chat.id, photo=data["photo"], caption=text
            )
            await state.update_data(summary_message_id=msg.message_id)
        except Exception:
            msg = await message_or_callback.answer(text)
            await state.update_data(summary_message_id=msg.message_id)
    else:
        msg = await message_or_callback.answer(text)
    await state.update_data(summary_message_id=msg.message_id)


async def delete_summary(message, state):
    """
    Function to delete the summary.
    """
    data = await state.get_data()
    summary_message_id = data.get("summary_message_id")
    if summary_message_id:
        try:
            await message.bot.delete_message(message.chat.id, summary_message_id)
        except Exception:
            pass
        await state.update_data(summary_message_id=None)
