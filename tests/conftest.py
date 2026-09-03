import pytest

from proofthread.database import create_engine_and_session, initialize_database
from proofthread.service import LedgerService


@pytest.fixture
async def runtime(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'proofthread-test.db'}"
    engine, sessions = create_engine_and_session(database_url)
    await initialize_database(engine)
    service = LedgerService(sessions, "UTC")
    try:
        yield service
    finally:
        await engine.dispose()
