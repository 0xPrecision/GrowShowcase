import os

DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:////data/shop.db")

TORTOISE_ORM = {
    "connections": {
        "default": DB_URL,
    },
    "apps": {
        "models": {
            "models": [
                "database.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}

