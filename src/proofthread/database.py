import argparse
import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import event, inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from proofthread.models import Base

LEGACY_SCHEMA_REVISION = "20260903_0001"
LEDGER_TABLES = {"chat_settings", "ledger_records", "ledger_events"}


def normalize_database_url(database_url: str) -> str:
    """Convert common provider URLs to SQLAlchemy's async PostgreSQL driver."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def ensure_sqlite_parent(database_url: str) -> None:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        return
    raw_path = database_url.removeprefix(prefix)
    if raw_path == ":memory:" or raw_path.startswith("file:"):
        return
    Path(raw_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def create_engine_and_session(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    database_url = normalize_database_url(database_url)
    ensure_sqlite_parent(database_url)
    engine = create_async_engine(database_url, pool_pre_ping=True)
    if database_url.startswith("sqlite+aiosqlite:///"):

        @event.listens_for(engine.sync_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


async def initialize_database(engine: AsyncEngine) -> None:
    """Create tables for isolated tests; production startup uses Alembic migrations."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


def run_migrations(database_url: str, revision: str = "head") -> None:
    database_url = normalize_database_url(database_url)
    ensure_sqlite_parent(database_url)
    repository_config = Path(__file__).resolve().parents[2] / "alembic.ini"
    packaged_config = Path(__file__).resolve().parent / "alembic.ini"
    config_path = repository_config if repository_config.is_file() else packaged_config
    if not config_path.is_file():
        raise RuntimeError(f"Alembic configuration not found at {config_path}")
    config = Config(config_path)
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

    tables = asyncio.run(_database_tables(database_url))
    if "alembic_version" not in tables and LEDGER_TABLES <= tables:
        command.stamp(config, LEGACY_SCHEMA_REVISION)
    elif "alembic_version" not in tables and LEDGER_TABLES & tables:
        raise RuntimeError(
            "A partial legacy schema was detected. Back up the database and repair it before "
            "running migrations."
        )
    command.upgrade(config, revision)


async def _database_tables(database_url: str) -> set[str]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            return set(
                await connection.run_sync(
                    lambda sync_connection: inspect(sync_connection).get_table_names()
                )
            )
    finally:
        await engine.dispose()


async def upgrade_database(database_url: str) -> None:
    await asyncio.to_thread(run_migrations, database_url)


def database_cli() -> None:
    from proofthread.config import get_settings

    parser = argparse.ArgumentParser(description="Manage the ProofThread database schema.")
    parser.add_argument("revision", nargs="?", default="head", help="Alembic target revision")
    args = parser.parse_args()
    settings = get_settings()
    run_migrations(settings.database_url, args.revision)
