from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from proofthread.models import Base


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
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
