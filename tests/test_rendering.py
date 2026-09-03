from datetime import UTC, datetime

from proofthread.models import LedgerRecord, RecordKind, RecordStatus
from proofthread.rendering import record_keyboard, render_digest, render_record


def record(kind: RecordKind, **overrides) -> LedgerRecord:
    values = {
        "id": "ABC123",
        "telegram_chat_id": -1001234567890,
        "thread_id": None,
        "kind": kind,
        "status": RecordStatus.OPEN,
        "text": "Ship <the> release",
        "source_message_id": 12,
        "source_excerpt": "Source",
        "source_link": "https://t.me/c/1234567890/12?a=1&b=2",
        "owner_user_id": 9,
        "owner_label": "@owner",
        "created_by_id": 7,
        "created_by_label": "Creator & team",
        "due_at": datetime(2026, 9, 10, 17, tzinfo=UTC),
        "reminder_sent_at": None,
        "supersedes_id": None,
        "closed_at": None,
    }
    values.update(overrides)
    return LedgerRecord(**values)


def test_render_record_escapes_content_and_includes_evidence() -> None:
    output = render_record(record(RecordKind.ACTION))

    assert "Ship &lt;the&gt; release" in output
    assert "Creator &amp; team" in output
    assert "Open source message" in output
    assert "2026-09-10" in output


def test_compact_record_omits_creator_and_source() -> None:
    output = render_record(record(RecordKind.DECISION), compact=True)

    assert "Captured by" not in output
    assert "Open source message" not in output


def test_keyboard_matches_record_lifecycle() -> None:
    action_keyboard = record_keyboard(record(RecordKind.ACTION))
    question_keyboard = record_keyboard(record(RecordKind.QUESTION))
    closed_keyboard = record_keyboard(record(RecordKind.ACTION, status=RecordStatus.COMPLETED))

    assert action_keyboard.inline_keyboard[0][0].callback_data == "pt:completed:ABC123"
    assert question_keyboard.inline_keyboard[0][0].callback_data == "pt:resolved:ABC123"
    assert closed_keyboard is None


def test_digest_groups_records_and_handles_empty_state() -> None:
    output = render_digest(
        [
            record(RecordKind.ACTION),
            record(RecordKind.QUESTION, id="DEF456", owner_label=None, due_at=None),
            record(RecordKind.DECISION, id="GHI789"),
        ]
    )

    assert "Actions" in output
    assert "Questions" in output
    assert "Decisions" in output
    assert "source" in output
    assert "Nothing is waiting" in render_digest([])
