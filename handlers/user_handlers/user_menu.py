from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers.user_handlers.user_catalog import show_products
from handlers.user_handlers.user_help import help_cmd
from handlers.user_handlers.user_profile import show_profile_menu
from utils.user_utils.universal_handlers import universal_exit
from utils.user_utils.user_common_utils import delete_user_message_safe

router = Router()


@router.callback_query(lambda c: c.data in ["menu_main", "menu_offers"])
async def universal_exit_handler(callback: CallbackQuery, state: FSMContext, t):
    """
    Universal handler for exiting any state via the “Main Menu” and “Catalog” buttons.
    """
    await universal_exit(callback, state, t)


@router.callback_query(F.data.startswith("menu_"))
async def menu_router(callback: CallbackQuery, state: FSMContext, t):
    """
    Routes clicks across the main menu sections.
    """
    action = callback.data.replace("menu_", "")
    await callback.message.delete()
    if action == "offers":
        await show_products(callback, t)
    elif action == "call":
        await show_profile_menu(callback, t)
    elif action == "help":
        await help_cmd(callback, state, t)
    await callback.answer()


@router.message(F.text)
async def text_catch_all_handler(message: Message, t, state: FSMContext, **_):
    """
    Catches any text when only a callback button is expected.
    Shows an alert and does not change the FSM state.
    """
    if message.text != "/start_admin":
        await delete_user_message_safe(message)
        msg = await message.answer(t("user_menu.messages.ispolzujte-knopki-vyshe"))
        await state.update_data(main_message_id=msg.message_id)
