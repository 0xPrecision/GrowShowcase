from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.user_kb.user_main_menu import main_menu
from utils.common_utils import delete_request_and_user_message


router = Router(name="start")


@router.message(CommandStart())
async def start_cmd(message: Message, t, state: FSMContext):
    """
    Main entry point
    """
    await delete_request_and_user_message(message, state)
    await state.clear()
    await message.answer(
        t("user_common.messages.b-dobro-pozhalovat-v-magazin-b"),
        reply_markup=main_menu(t),
    )
