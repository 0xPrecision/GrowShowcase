import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from aerich import Command
from tortoise import Tortoise, connections

try:
    from database.config import TORTOISE_ORM
except Exception as e:
    raise RuntimeError(
        "config.TORTOISE_ORM not found. Create config.py with Tortoise settings."
    ) from e


# -------------------------
# ENV switches for prod
# -------------------------
AERICH_AUTO_UPGRADE = os.getenv("AERICH_AUTO_UPGRADE", "false").lower() in {"1", "true", "yes"}
INIT_DB_ALLOW_GENERATE = os.getenv("INIT_DB_ALLOW_GENERATE", "false").lower() in {"1", "true", "yes"}
BACKUP_BEFORE_MIGRATE = os.getenv("BACKUP_BEFORE_MIGRATE", "true").lower() in {"1", "true", "yes"}


def _sqlite_file_from_url(db_url: str) -> Optional[Path]:
    """
    Extract the SQLite file path from a sqlite:// URL.
    Supports:
      - sqlite://shop.db
      - sqlite:///abs/path/shop.db
      - sqlite:////really/abs/path/shop.db  (нормализуется Path'ом)
    Ignores :memory:
    """
    if not db_url.startswith("sqlite://"):
        return None
    rest = db_url[len("sqlite://") :]
    # :memory: или пустые/служебные
    if not rest or rest.strip() == ":memory:":
        return None
    # Нормализуем путь
    return Path(rest).resolve() if rest.startswith("/") else Path(rest).resolve()


def _is_sqlite(db_url: str) -> bool:
    return db_url.startswith("sqlite://")


def _sqlite_backup_path(db_path: Path) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return backup_dir / f"{db_path.stem}_backup_{ts}{db_path.suffix or '.db'}"


def backup_sqlite_db(db_url: str) -> None:
    """
    Create a backup of the SQLite database before running migrations.
    Backup goes to <db_dir>/backups/<name>_backup_YYYYmmdd_HHMMSS.db
    """
    if not BACKUP_BEFORE_MIGRATE:
        return
    db_path = _sqlite_file_from_url(db_url)
    if not db_path:
        return
    if db_path.exists():
        shutil.copy2(db_path, _sqlite_backup_path(db_path))


async def _apply_sqlite_pragmas() -> None:
    """
    For SQLite only: enable WAL, foreign_keys, and reasonable sync level.
    Safe to call repeatedly.
    """
    try:
        conn = connections.get("default")
        # journal_mode=WAL возвращает строку с текущим режимом
        await conn.execute_query("PRAGMA foreign_keys=ON;")
        await conn.execute_query("PRAGMA journal_mode=WAL;")
        await conn.execute_query("PRAGMA synchronous=NORMAL;")
        await conn.execute_query("PRAGMA temp_store=MEMORY;")
    except Exception:
        # В худшем случае просто продолжаем без PRAGMA
        pass


async def init_db() -> None:
    """
    Initialize DB:
      1) If SQLite and file exists -> backup (optional).
      2) If AERICH_AUTO_UPGRADE=true and migrations exist -> aerich upgrade.
      3) Else:
         - If DB not exists and INIT_DB_ALLOW_GENERATE=true -> generate schemas.
         - Otherwise just init connections.
      4) Apply SQLite PRAGMAs when applicable.
    """
    db_url = TORTOISE_ORM["connections"]["default"]
    db_path = _sqlite_file_from_url(db_url)
    db_exists = bool(db_path and db_path.exists())

    # 1) Backup for SQLite
    if _is_sqlite(db_url) and db_exists:
        backup_sqlite_db(db_url)

    migrations_root = Path("migrations")
    has_migrations = migrations_root.exists() and any(migrations_root.glob("**/*.json"))

    if AERICH_AUTO_UPGRADE and has_migrations:
        # Прогоним миграции через Aerich из приложения только если это явно разрешено
        cmd = Command(
            tortoise_config=TORTOISE_ORM, app="models", location=str(migrations_root)
        )
        await cmd.init()
        await cmd.upgrade()
        # После апгрейда просто подключимся
        await Tortoise.init(config=TORTOISE_ORM)
    else:
        # Без автоката миграций: честно инициализируемся
        if not db_exists:
            if INIT_DB_ALLOW_GENERATE:
                await Tortoise.init(config=TORTOISE_ORM)
                await Tortoise.generate_schemas()
            else:
                # В проде лучше знать об отсутствии схем заранее
                # но чтобы не вываливаться насмерть — подключимся, а отсутствие таблиц проявится явно
                await Tortoise.init(config=TORTOISE_ORM)
        else:
            await Tortoise.init(config=TORTOISE_ORM)

    # 4) SQLite PRAGMAs
    if _is_sqlite(db_url):
        await _apply_sqlite_pragmas()


async def close_db() -> None:
    """Close all database connections cleanly."""
    await Tortoise.close_connections()
