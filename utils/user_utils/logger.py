import logging
import sys

# Общая конфигурация логирования
logging.basicConfig(
    level=logging.INFO,  # можно DEBUG для разработки
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # вывод в консоль
        logging.FileHandler("bot.log", encoding="utf-8"),  # лог-файл
    ],
)

# Создаём именованный логгер для проекта
logger = logging.getLogger("shop_bot")
