from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from database.crud import create_review
from handlers.admin_handlers.admin_access import admin_only
from states.admin_states.product_states import AddReviewStates
from utils.common_utils import delete_request_and_user_message

router = Router()


@router.callback_query(F.data == "admin_add_review")
@admin_only
async def admin_products_list(callback: CallbackQuery, state: FSMContext, t):
    await delete_request_and_user_message(callback.message, state)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("order_keyboards.buttons.v-glavnoe-menyu"),
            callback_data="/start_admin")]])

    msg = await callback.message.answer(t("add_review_picture"), reply_markup=kb)
    await state.set_state(AddReviewStates.waiting_photo)
    await state.update_data(main_message_id=msg.message_id)
    await callback.answer()


@router.message(AddReviewStates.waiting_photo, F.photo)
@admin_only
async def add_product_photo(message: Message, state: FSMContext, t):
    await delete_request_and_user_message(message, state)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("order_keyboards.buttons.v-glavnoe-menyu"),
            callback_data="/start_admin")]])
    photo = message.photo[-1].file_id
    await create_review(int(photo))
    msg = await message.answer("✅", reply_markup=kb)
    await state.update_data(main_message_id=msg.message_id)
    await state.clear()