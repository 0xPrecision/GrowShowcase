import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/shop.db")

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL,
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
