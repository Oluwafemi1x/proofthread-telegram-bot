from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from proofthread.models import LedgerEvent, RecordKind, RecordStatus
from proofthread.service import Actor, InvalidTransition, LedgerService, RecordNotFound


async def create_record(service: LedgerService, kind: RecordKind = RecordKind.ACTION):
    return await service.create_record(
        chat_id=-1001234567890,
        thread_id=None,
        kind=kind,
        text="Publish the first release",
        source_message_id=12,
        source_excerpt="We should publish on Friday.",
        source_link="https://t.me/c/1234567890/12",
        actor=Actor(7, "@creator"),
        owner_user_id=9,
        owner_label="@owner",
        due_at=datetime.now(UTC) + timedelta(days=1),
    )


async def test_create_list_and_export(runtime: LedgerService) -> None:
    record = await create_record(runtime)

    records = await runtime.list_records(-1001234567890, statuses=[RecordStatus.OPEN])
    exported = await runtime.export_records(-1001234567890)

    assert [item.id for item in records] == [record.id]
    assert exported[0]["source_link"].endswith("/12")
    assert exported[0]["owner"] == "@owner"


async def test_complete_action(runtime: LedgerService) -> None:
    record = await create_record(runtime)

    updated = await runtime.transition(
        chat_id=record.telegram_chat_id,
        record_id=record.id[:6],
        actor=Actor(9, "@owner"),
        target=RecordStatus.COMPLETED,
    )

    assert updated.status == RecordStatus.COMPLETED
    assert updated.closed_at is not None


async def test_reject_invalid_transition(runtime: LedgerService) -> None:
    record = await create_record(runtime, RecordKind.QUESTION)

    with pytest.raises(InvalidTransition):
        await runtime.transition(
            chat_id=record.telegram_chat_id,
            record_id=record.id,
            actor=Actor(7, "@creator"),
            target=RecordStatus.COMPLETED,
        )


async def test_supersede_decision(runtime: LedgerService) -> None:
    original = await create_record(runtime, RecordKind.DECISION)

    replacement = await runtime.create_record(
        chat_id=original.telegram_chat_id,
        thread_id=None,
        kind=RecordKind.DECISION,
        text="Publish on Monday instead",
        source_message_id=13,
        source_excerpt=None,
        source_link=None,
        actor=Actor(7, "@creator"),
        supersedes_id=original.id,
    )

    old = await runtime.get_record(original.telegram_chat_id, original.id)
    assert old.status == RecordStatus.SUPERSEDED
    assert replacement.supersedes_id == original.id


async def test_record_ids_are_scoped_to_chat(runtime: LedgerService) -> None:
    record = await create_record(runtime)

    with pytest.raises(RecordNotFound):
        await runtime.get_record(-1009999999999, record.id)


async def test_deleting_record_cascades_to_event_history(runtime: LedgerService) -> None:
    record = await create_record(runtime)

    await runtime.delete_record(record.telegram_chat_id, record.id)

    async with runtime.sessions() as session:
        count = await session.scalar(
            select(func.count()).select_from(LedgerEvent).where(LedgerEvent.record_id == record.id)
        )
    assert count == 0


async def test_chat_settings_can_be_created_updated_and_read(runtime: LedgerService) -> None:
    created = await runtime.ensure_chat(-1001, "Launch team")
    updated = await runtime.ensure_chat(-1001, "Launch room")

    assert created.telegram_chat_id == -1001
    assert updated.title == "Launch room"
    assert await runtime.chat_timezone(-1001) == "UTC"
    assert await runtime.chat_timezone(-9999) == "UTC"


async def test_chat_timezone_can_be_changed(runtime: LedgerService) -> None:
    created = await runtime.set_chat_timezone(-1002, "Africa/Lagos")
    updated = await runtime.set_chat_timezone(-1002, "Europe/London")

    assert created.telegram_chat_id == -1002
    assert updated.timezone == "Europe/London"
    assert await runtime.chat_timezone(-1002) == "Europe/London"


async def test_invalid_timezone_is_rejected(runtime: LedgerService) -> None:
    with pytest.raises(ValueError, match="Unknown timezone"):
        await runtime.set_chat_timezone(-1003, "Mars/Olympus_Mons")


@pytest.mark.parametrize("text", ["x", "a" * 1001])
async def test_record_text_length_is_validated(runtime: LedgerService, text: str) -> None:
    with pytest.raises(ValueError, match="between 3 and 1000"):
        await runtime.create_record(
            chat_id=-1001234567890,
            thread_id=None,
            kind=RecordKind.ACTION,
            text=text,
            source_message_id=12,
            source_excerpt=None,
            source_link=None,
            actor=Actor(7, "@creator"),
        )


async def test_closed_record_cannot_transition_again(runtime: LedgerService) -> None:
    record = await create_record(runtime)
    await runtime.transition(
        chat_id=record.telegram_chat_id,
        record_id=record.id,
        actor=Actor(9, "@owner"),
        target=RecordStatus.COMPLETED,
    )

    with pytest.raises(InvalidTransition, match="already completed"):
        await runtime.transition(
            chat_id=record.telegram_chat_id,
            record_id=record.id,
            actor=Actor(9, "@owner"),
            target=RecordStatus.CANCELLED,
        )


async def test_due_reminders_are_marked_once(runtime: LedgerService) -> None:
    due = await runtime.create_record(
        chat_id=-1001234567890,
        thread_id=None,
        kind=RecordKind.ACTION,
        text="Deploy production",
        source_message_id=12,
        source_excerpt=None,
        source_link=None,
        actor=Actor(7, "@creator"),
        due_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    await runtime.create_record(
        chat_id=-1001234567890,
        thread_id=None,
        kind=RecordKind.ACTION,
        text="Deploy next month",
        source_message_id=13,
        source_excerpt=None,
        source_link=None,
        actor=Actor(7, "@creator"),
        due_at=datetime.now(UTC) + timedelta(days=30),
    )

    waiting = await runtime.due_reminders(15)
    await runtime.mark_reminded(due.id)

    assert [item.id for item in waiting] == [due.id]
    assert await runtime.due_reminders(15) == []


async def test_missing_record_cannot_be_deleted(runtime: LedgerService) -> None:
    with pytest.raises(RecordNotFound):
        await runtime.delete_record(-1001234567890, "NOTFOUND")
