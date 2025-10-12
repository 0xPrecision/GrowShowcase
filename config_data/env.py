import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = os.getenv("ADMIN_IDS")

ADMIN_IDS = [int(x) for x in ADMIN_IDS.split(",") if x.strip().isdigit()]
