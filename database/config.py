import os

TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://shop.db",
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

