from pathlib import Path

from sqlalchemy import inspect

from proofthread.database import (
    create_engine_and_session,
    initialize_database,
    normalize_database_url,
    run_migrations,
)


def test_normalize_common_postgresql_urls() -> None:
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )


def test_normalize_preserves_explicit_driver_and_sqlite() -> None:
    async_url = "postgresql+asyncpg://user:pass@host/db"
    sqlite_url = "sqlite+aiosqlite:///:memory:"

    assert normalize_database_url(async_url) == async_url
    assert normalize_database_url(sqlite_url) == sqlite_url


def test_initial_migration_builds_schema(tmp_path: Path) -> None:
    from sqlalchemy import create_engine

    database_path = tmp_path / "migration.db"
    async_url = f"sqlite+aiosqlite:///{database_path}"
    run_migrations(async_url)

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert {"alembic_version", "chat_settings", "ledger_records", "ledger_events"} <= tables


def test_migrations_adopt_pre_alembic_schema(tmp_path: Path) -> None:
    import asyncio

    from sqlalchemy import create_engine, text

    database_path = tmp_path / "legacy.db"
    async_url = f"sqlite+aiosqlite:///{database_path}"

    async def create_legacy_schema() -> None:
        engine, _sessions = create_engine_and_session(async_url)
        try:
            await initialize_database(engine)
        finally:
            await engine.dispose()

    asyncio.run(create_legacy_schema())
    run_migrations(async_url)

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        with engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        engine.dispose()

    assert revision == "20260903_0001"
