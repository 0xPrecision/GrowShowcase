from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.user_kb.user_checkout_keyboards import use_username
from keyboards.user_kb.user_common_keyboards import cart_back_menu
from utils.common_utils import delete_request_and_user_message


async def delete_user_message_safe(message: Message) -> None:
    """
    Safely deletes the user_kb's message.
    """
    try:
        await message.delete()
    except Exception:
        pass


async def start_manual_checkout(message_or_callback, state: FSMContext, t, username, **_):
    """
    Full name handler for checkout, supports edit mode.
    After successful input, immediately shows the comment step (if not edit).
    Messages are always cleared.
    """
    if hasattr(message_or_callback, "message"):
        target_message = message_or_callback.message
    else:
        target_message = message_or_callback
    await delete_request_and_user_message(target_message, state)
    main_msg = await target_message.answer(
        t("user_common_utils.messages.zapolnite-dannye-1-fio"),
        reply_markup=use_username(t, username)
    )
    await state.update_data(main_message_id=main_msg.message_id)


async def validation_process_name(message: Message, state: FSMContext, t, **_):
    """
    Shows a warning about an invalid full name.
    :param message: User message.
    :param state: FSMContext for storing main_message_id.
    """
    warn = await message.answer(
        t("user_common_utils.messages.vvedite-korrektnoe-imya-tolko"),
        reply_markup=cart_back_menu(t),
    )
    await state.update_data(main_message_id=warn.message_id)



async def send_step_and_cleanup(
    message: Message,
    text: str,
    state: FSMContext,
    reply_markup=None,
    main_message_id_key: str = "main_message_id",
) -> None:
    """
    Universal step sender: sends a message, deletes the old one, and saves main_message_id.

    :param message: User message.
    :param text: Text to send.
    :param state: FSMContext.
    :param reply_markup: Keyboard (default None).
    :param main_message_id_key: Key for storing the id (default main_message_id).
    """
    msg = await message.answer(text, reply_markup=reply_markup)
    await delete_user_message_safe(message)
    await state.update_data(**{main_message_id_key: msg.message_id})
