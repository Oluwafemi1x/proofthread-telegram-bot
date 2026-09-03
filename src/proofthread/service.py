from __future__ import annotations

import secrets
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from proofthread.models import ChatSettings, LedgerEvent, LedgerRecord, RecordKind, RecordStatus


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: int
    label: str


class RecordNotFound(LookupError):
    pass


class InvalidTransition(ValueError):
    pass


class LedgerService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession], default_timezone: str = "UTC"):
        self.sessions = sessions
        self.default_timezone = default_timezone

    async def ensure_chat(self, chat_id: int, title: str | None) -> ChatSettings:
        async with self.sessions.begin() as session:
            chat = await session.get(ChatSettings, chat_id)
            if chat is None:
                chat = ChatSettings(
                    telegram_chat_id=chat_id,
                    title=title,
                    timezone=self.default_timezone,
                )
                session.add(chat)
            elif title and title != chat.title:
                chat.title = title
            return chat

    async def chat_timezone(self, chat_id: int) -> str:
        async with self.sessions() as session:
            chat = await session.get(ChatSettings, chat_id)
            return chat.timezone if chat else self.default_timezone

    async def set_chat_timezone(self, chat_id: int, timezone_name: str) -> ChatSettings:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone. Use a name such as Africa/Lagos or UTC.") from exc
        async with self.sessions.begin() as session:
            chat = await session.get(ChatSettings, chat_id)
            if chat is None:
                chat = ChatSettings(
                    telegram_chat_id=chat_id,
                    timezone=timezone_name,
                )
                session.add(chat)
            else:
                chat.timezone = timezone_name
            return chat

    async def create_record(
        self,
        *,
        chat_id: int,
        thread_id: int | None,
        kind: RecordKind,
        text: str,
        source_message_id: int,
        source_excerpt: str | None,
        source_link: str | None,
        actor: Actor,
        owner_user_id: int | None = None,
        owner_label: str | None = None,
        due_at: datetime | None = None,
        supersedes_id: str | None = None,
    ) -> LedgerRecord:
        clean_text = " ".join(text.split()).strip()
        if not 3 <= len(clean_text) <= 1000:
            raise ValueError("Record text must contain between 3 and 1000 characters.")

        async with self.sessions.begin() as session:
            if supersedes_id:
                previous = await self._get_record(session, chat_id, supersedes_id)
                if previous.kind is not RecordKind.DECISION:
                    raise InvalidTransition("Only a decision can be superseded.")
                previous.status = RecordStatus.SUPERSEDED
                previous.closed_at = datetime.now(UTC)
                session.add(
                    LedgerEvent(
                        record_id=previous.id,
                        event_type="superseded",
                        actor_user_id=actor.user_id,
                        actor_label=actor.label,
                        detail={},
                    )
                )

            record = LedgerRecord(
                id=secrets.token_hex(6).upper(),
                telegram_chat_id=chat_id,
                thread_id=thread_id,
                kind=kind,
                text=clean_text,
                source_message_id=source_message_id,
                source_excerpt=(source_excerpt or "")[:320] or None,
                source_link=source_link,
                owner_user_id=owner_user_id,
                owner_label=owner_label,
                created_by_id=actor.user_id,
                created_by_label=actor.label,
                due_at=due_at,
                supersedes_id=supersedes_id,
            )
            session.add(record)
            session.add(
                LedgerEvent(
                    record_id=record.id,
                    event_type="created",
                    actor_user_id=actor.user_id,
                    actor_label=actor.label,
                    detail={"kind": kind.value},
                )
            )
            return record

    async def list_records(
        self,
        chat_id: int,
        *,
        kinds: Iterable[RecordKind] | None = None,
        statuses: Iterable[RecordStatus] | None = None,
        owner_user_id: int | None = None,
        limit: int = 20,
    ) -> list[LedgerRecord]:
        clauses = [LedgerRecord.telegram_chat_id == chat_id]
        if kinds:
            clauses.append(LedgerRecord.kind.in_(list(kinds)))
        if statuses:
            clauses.append(LedgerRecord.status.in_(list(statuses)))
        if owner_user_id is not None:
            clauses.append(LedgerRecord.owner_user_id == owner_user_id)
        statement = (
            select(LedgerRecord)
            .where(and_(*clauses))
            .order_by(LedgerRecord.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        async with self.sessions() as session:
            return list((await session.scalars(statement)).all())

    async def get_record(self, chat_id: int, record_id: str) -> LedgerRecord:
        async with self.sessions() as session:
            return await self._get_record(session, chat_id, record_id)

    async def _get_record(
        self, session: AsyncSession, chat_id: int, record_id: str
    ) -> LedgerRecord:
        normalized = record_id.strip().upper()
        statement = select(LedgerRecord).where(
            LedgerRecord.telegram_chat_id == chat_id,
            LedgerRecord.id.like(f"{normalized}%"),
        )
        matches = list((await session.scalars(statement)).all())
        if len(matches) != 1:
            raise RecordNotFound("Record ID was not found or is ambiguous.")
        return matches[0]

    async def transition(
        self,
        *,
        chat_id: int,
        record_id: str,
        actor: Actor,
        target: RecordStatus,
    ) -> LedgerRecord:
        allowed = {
            RecordKind.ACTION: {RecordStatus.COMPLETED, RecordStatus.CANCELLED},
            RecordKind.QUESTION: {RecordStatus.RESOLVED, RecordStatus.CANCELLED},
            RecordKind.DECISION: {RecordStatus.CANCELLED},
        }
        async with self.sessions.begin() as session:
            record = await self._get_record(session, chat_id, record_id)
            if record.status is not RecordStatus.OPEN:
                raise InvalidTransition(f"Record is already {record.status.value}.")
            if target not in allowed[record.kind]:
                raise InvalidTransition(f"A {record.kind.value} cannot become {target.value}.")
            record.status = target
            record.closed_at = datetime.now(UTC)
            session.add(
                LedgerEvent(
                    record_id=record.id,
                    event_type=target.value,
                    actor_user_id=actor.user_id,
                    actor_label=actor.label,
                    detail={},
                )
            )
            return record

    async def due_reminders(self, window_minutes: int) -> list[LedgerRecord]:
        now = datetime.now(UTC)
        cutoff = now + timedelta(minutes=window_minutes)
        statement = (
            select(LedgerRecord)
            .where(
                LedgerRecord.kind == RecordKind.ACTION,
                LedgerRecord.status == RecordStatus.OPEN,
                LedgerRecord.due_at.is_not(None),
                LedgerRecord.due_at <= cutoff,
                LedgerRecord.reminder_sent_at.is_(None),
            )
            .order_by(LedgerRecord.due_at.asc())
            .limit(100)
        )
        async with self.sessions() as session:
            return list((await session.scalars(statement)).all())

    async def mark_reminded(self, record_id: str) -> None:
        async with self.sessions.begin() as session:
            record = await session.get(LedgerRecord, record_id)
            if record:
                record.reminder_sent_at = datetime.now(UTC)

    async def delete_record(self, chat_id: int, record_id: str) -> str:
        async with self.sessions.begin() as session:
            record = await self._get_record(session, chat_id, record_id)
            exact_id = record.id
            await session.delete(record)
            return exact_id

    async def export_records(self, chat_id: int) -> list[dict[str, object]]:
        records = await self.list_records(chat_id, limit=100)
        return [
            {
                "id": item.id,
                "kind": item.kind.value,
                "status": item.status.value,
                "text": item.text,
                "owner": item.owner_label,
                "due_at": item.due_at.isoformat() if item.due_at else None,
                "source_link": item.source_link,
                "created_by": item.created_by_label,
                "created_at": item.created_at.isoformat(),
                "closed_at": item.closed_at.isoformat() if item.closed_at else None,
            }
            for item in records
        ]
