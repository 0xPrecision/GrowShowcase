from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from config_data.env import TELEGRAM_BOT_TOKEN

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
