from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto

from database.crud import get_all_reviews, get_review_by_index
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from utils.user_utils.common_utils import delete_request_and_user_message

from keyboards.user_kb.user_profile_keyboards import profile_menu_keyboard, reviews_kb
from utils.user_utils.user_profile_utils import ReviewsCB

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
async def open_reviews(callback: CallbackQuery, t):
    await callback.answer()
    total = await get_all_reviews()
    if total == 0:
        await callback.message.answer("No Reviews", reply_markup=cart_back_menu(t))
        return

    idx = 0
    review = await get_review_by_index(idx)
    kb = reviews_kb(idx, total, contact_url="https://t.me/TGStoreLab")

    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=review.file_id),
            reply_markup=kb,
        )
    except Exception:
        # если исходное сообщение не с медиа и редактировать нельзя — просто отправим новое фото
        await callback.message.answer_photo(photo=review.file_id, reply_markup=kb)


# 5) Листание вперёд/назад
@router.callback_query(ReviewsCB.filter(F.action.in_({"next", "prev"})))
async def paginate_reviews(callback: CallbackQuery, callback_data: ReviewsCB):
    await callback.answer()
    total = await get_all_reviews()
    if total == 0:
        await callback.message.edit_text("Пока отзывов нет.")
        return

    idx = callback_data.index % total
    review = await get_review_by_index(idx)
    kb = reviews_kb(idx, total, contact_url="https://t.me/TGStoreLab")

    # меняем картинку в том же сообщении
    await callback.message.edit_media(
        media=InputMediaPhoto(media=review.file_id),
        reply_markup=kb,
    )

