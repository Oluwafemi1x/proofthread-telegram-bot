from unittest.mock import AsyncMock

from proofthread.models import RecordKind
from proofthread.reminders import send_due_reminders
from proofthread.service import Actor


async def test_successful_reminder_is_marked(runtime) -> None:
    record = await runtime.create_record(
        chat_id=-1001234567890,
        thread_id=99,
        kind=RecordKind.ACTION,
        text="Deploy the release",
        source_message_id=12,
        source_excerpt=None,
        source_link=None,
        actor=Actor(7, "@creator"),
    )
    runtime.due_reminders = AsyncMock(return_value=[record])
    runtime.mark_reminded = AsyncMock()
    bot = AsyncMock()

    await send_due_reminders(bot, runtime, 15)

    bot.send_message.assert_awaited_once()
    runtime.mark_reminded.assert_awaited_once_with(record.id)


async def test_failed_reminder_is_retried_later(runtime) -> None:
    record = await runtime.create_record(
        chat_id=-1001234567890,
        thread_id=None,
        kind=RecordKind.ACTION,
        text="Deploy the release",
        source_message_id=12,
        source_excerpt=None,
        source_link=None,
        actor=Actor(7, "@creator"),
    )
    runtime.due_reminders = AsyncMock(return_value=[record])
    runtime.mark_reminded = AsyncMock()
    bot = AsyncMock()
    bot.send_message.side_effect = RuntimeError("Telegram unavailable")

    await send_due_reminders(bot, runtime, 15)

    runtime.mark_reminded.assert_not_awaited()
