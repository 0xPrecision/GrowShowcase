import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from aerich import Command
from tortoise import Tortoise

try:
    from database.config import TORTOISE_ORM
except Exception as e:
    raise RuntimeError(
        "config.TORTOISE_ORM not found. Create config.py with Tortoise settings."
    ) from e


def _sqlite_file_from_url(db_url: str) -> Optional[Path]:
    """
    Extract the SQLite file path from a sqlite:// URL.
    Supports both relative ('sqlite://shop.db') and absolute ('sqlite:///abs/path/shop.db') paths.
    """
    if not db_url.startswith("sqlite://"):
        return None
    rest = db_url[len("sqlite://") :]
    return Path(rest)


def backup_sqlite_db(db_url: str) -> None:
    """
    Create a backup of the SQLite database before running migrations.

    Args:
        db_url (str): Database URL (must be SQLite).
    """
    db_path = _sqlite_file_from_url(db_url)
    if not db_path:
        return
    if db_path.exists():
        backup_dir = Path("backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(db_path, backup_dir / f"shop_backup_{ts}.db")


async def init_db() -> None:
    """
    Initialize the database properly:
    1. Backup SQLite file if it exists.
    2. If migrations exist — run `aerich upgrade`.
    3. If no migrations and database does not exist — run `generate_schemas()` once.
    4. If database exists but no migrations — just connect and continue.
    """
    db_url = TORTOISE_ORM["connections"]["default"]
    db_path = _sqlite_file_from_url(db_url)
    db_exists = bool(db_path and db_path.exists())

    if db_exists:
        backup_sqlite_db(db_url)

    migrations_root = Path("migrations")

    if migrations_root.exists() and any(migrations_root.glob("**/*.json")):
        cmd = Command(
            tortoise_config=TORTOISE_ORM, app="models", location=str(migrations_root)
        )
        await cmd.init()
        await cmd.upgrade()
    else:
        if not db_exists:
            await Tortoise.init(config=TORTOISE_ORM)
            await Tortoise.generate_schemas()
        else:
            await Tortoise.init(config=TORTOISE_ORM)


async def close_db() -> None:
    """
    Close all database connections cleanly.
    """
    await Tortoise.close_connections()

# from pathlib import Path
#
# from aerich import Command
# from tortoise import Tortoise
#
# try:
#     from database.config import TORTOISE_ORM
# except Exception as e:
#     raise RuntimeError(
#         "config.TORTOISE_ORM not found. Create config.py with Tortoise settings."
#     ) from e
#
#
# def _db_scheme() -> str:
#     url = TORTOISE_ORM["connections"]["default"]
#     # tortoise понимает и postgresql://, и postgres://
#     if url.startswith("postgres://") or url.startswith("postgresql://"):
#         return "postgres"
#     if url.startswith("sqlite://"):
#         return "sqlite"
#     return "other"
#
#
# async def init_db() -> None:
#     """
#     Инициализация БД для PostgreSQL (и не только):
#     1) Если есть миграции aerich -> `aerich upgrade`.
#     2) Если миграций нет -> одноразовый `generate_schemas()` (создаст таблицы).
#     3) Если БД/схема уже существует -> просто подключится.
#     """
#     scheme = _db_scheme()
#     migrations_root = Path("migrations").resolve()
#
#     has_migrations = migrations_root.exists() and any(
#         migrations_root.glob("**/*.json")
#     )
#
#     if has_migrations:
#         # Нормальный путь для продакшена: миграции рулит aerich
#         cmd = Command(
#             tortoise_config=TORTOISE_ORM,
#             app="models",
#             location=str(migrations_root)
#         )
#         await cmd.init()
#         await cmd.upgrade()
#         # После апгрейда держим коннект открыт для приложения
#         await Tortoise.init(config=TORTOISE_ORM)
#     else:
#         # Дев-путь/первый старт: просто создать схемы
#         # Для Postgres это сработает, если БД существует.
#         # Создание самой БД (CREATE DATABASE) здесь не делаем сознательно.
#         await Tortoise.init(config=TORTOISE_ORM)
#         await Tortoise.generate_schemas(safe=True)
#
#
# async def close_db() -> None:
#     """Нормально закрыть коннекты."""
#     await Tortoise.close_connections()

