from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import EMOJI_MAP
from database.models import Product

from keyboards.admin.catalog_keyboards import (
    back_menu,
    back_to_search_keyboard,
    product_admin_keyboard,
    show_products_for_search,
)
from states.admin_states.product_states import ProductSearchStates
from utils.common_utils import delete_request_and_user_message, format_price
from .admin_access import admin_only

router = Router()


@router.callback_query(F.data == "admin_search_product")
@admin_only
async def start_search_product(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Starts the FSM for product search.
    """
    msg = await callback.message.edit_text(
        t("search_product.messages.vvedite-nazvanie-tovara"), reply_markup=back_menu(t)
    )
    await state.update_data(main_message_id=msg.message_id)
    await state.set_state(ProductSearchStates.waiting_query)
    await callback.answer()


@router.message(ProductSearchStates.waiting_query)
@admin_only
async def search_product_query(message: Message, t, state: FSMContext, **_):
    """
    Searches for a product by the entered text or ID.
    """
    await delete_request_and_user_message(message, state)
    query = message.text.strip()
    if query.isdigit():
        products = await Product.filter(id=int(query)).all()
    else:
        products = await Product.filter(name__icontains=query).all()
    if not products:
        msg = await message.answer(
            t("search_product.messages.nichego-ne-najdeno-poprobujte"),
            reply_markup=back_to_search_keyboard(t),
        )
        await state.update_data(main_message_id=msg.message_id)
        await state.clear()
        return
    if len(products) == 1:
        product = products[0]
        await product.fetch_related("category")
        product_name = product.name
        pr_price = format_price(product.price)
        pr_descr = t(product.description) or "—"
        label = EMOJI_MAP.get(product.id, "📦")
        text = t("admin_catalog.misc.b-tovar-b-b-b-ostatok-kategoriya").format(
            product_name=f"{label} {product_name}",
            price=pr_price,
            currency=t("currency"),
            description=pr_descr
        )
        if product.photo:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=product.photo,
                caption=text,
                reply_markup=await product_admin_keyboard(product.id, t),
            )
        else:
            msg = await message.answer(
                text, reply_markup=await product_admin_keyboard(product.id, t)
            )
            await state.update_data(main_message_id=msg.message_id)
        await state.clear()
    else:
        await message.answer(
            t("search_order.naydeno-tovarov").format(products=len(products)),
            reply_markup=show_products_for_search(products, t),
        )
        await state.clear()
