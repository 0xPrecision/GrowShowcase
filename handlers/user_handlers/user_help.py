from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.user_kb.user_main_menu import main_menu
from utils.user_utils.common_utils import delete_request_and_user_message

router = Router()


async def help_cmd(callback: CallbackQuery, state: FSMContext, t, **_):
    """
    Sends the user_kb a help message about the store operation.
    """
    await delete_request_and_user_message(callback.message, state)
    await callback.bot.send_message(
        callback.from_user.id,
        t("user_help.messages.b-eto-demo-magazin-v"),
        reply_markup=main_menu(t),
    )
