import asyncio
import logging
from pathlib import Path

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from handlers.admin_handlers import router as admin_router
from handlers.user_handlers import router as user_router
from config_data.bot_instance import bot
from database.init_db import close_db, init_db
from services.i18n.middleware import LocaleMiddleware
from services.i18n.translations import Translator
from services.locale_repo import LocaleRepo


async def main():
    """
    Main entry point of the bot: initializes the database, starts the bot,
    and properly closes connections.
    """
    storage = RedisStorage.from_url("redis://localhost:6379/0")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    await init_db()

    translator = Translator(
        locales_dir=Path("locales").resolve(),
        default_locale="ru",
        supported=("ru", "en"),
    )
    locale_repo = LocaleRepo()
    dp = Dispatcher(storage=storage)
    dp.update.middleware.register(LocaleMiddleware(translator, locale_repo))

    dp.include_router(admin_router)
    dp.include_router(user_router)

    logging.info("Bot started polling")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        try:
            await bot.session.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
