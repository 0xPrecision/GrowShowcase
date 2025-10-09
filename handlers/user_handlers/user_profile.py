from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from utils.user_utils.common_utils import delete_request_and_user_message

from keyboards.user_kb.user_profile_keyboards import profile_menu_keyboard

router = Router()

@router.callback_query(F.data == "menu_call")
async def show_profile_menu(callback: CallbackQuery, state: FSMContext, t):
    """
    Displays the reviews & contacts.
    """
    await state.clear()
    await delete_request_and_user_message(callback.message, state)
    text = t("user_profile.misc.b-vy-v")
    msg = await callback.message.answer(text, reply_markup=profile_menu_keyboard(t))
    await state.update_data(main_message_id=msg.message_id)
    await callback.answer()


@router.callback_query(F.data == "reviews")
async def show_profile_orders_menu(callback: CallbackQuery, t, state: FSMContext, **_):
    """
    Displays the reviews.
    """
    await delete_request_and_user_message(callback.message, state)
    # sent_message = await callback.bot.send_message()
    await callback.answer()

