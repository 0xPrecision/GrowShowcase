from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.admin.admin_menu import admin_main_menu

from .admin_access import admin_only

router = Router()


@router.message(or_f(F.text == "/start_admin", F.data == "/start_admin"))
@router.callback_query(or_f(F.data == "/start_admin", F.text == "/start_admin"))
@admin_only
async def admin_panel_open(event: Message | CallbackQuery, t, state: FSMContext, **_):
    """
    Generic handler for opening the admin menu.
    Works for both messages and callback buttons.
    """
    await state.clear()
    if hasattr(event, "message"):
        msg = event.message
        edit = True
    else:
        msg = event
        edit = False
    if edit:
        await msg.edit_text(
            t("admin_common.messages.admin-panel-vyberite-dejstvie"),
            reply_markup=admin_main_menu(t),
        )
        await event.answer()
    else:
        await msg.answer(
            t("admin_common.messages.admin-panel-vyberite-dejstvie"),
            reply_markup=admin_main_menu(t),
        )


@router.message(F.text == "/start_admin")
@admin_only
async def admin_panel_message(message: Message, state: FSMContext):
    await admin_panel_open(message, state)


@router.callback_query(F.data == "/start_admin")
@admin_only
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    await admin_panel_open(callback, state)
