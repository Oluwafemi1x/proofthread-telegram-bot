from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class RecordKind(StrEnum):
    DECISION = "decision"
    ACTION = "action"
    QUESTION = "question"


class RecordStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class ChatSettings(Base):
    __tablename__ = "chat_settings"

    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LedgerRecord(Base):
    __tablename__ = "ledger_records"
    __table_args__ = (
        Index("ix_record_chat_status_kind", "telegram_chat_id", "status", "kind"),
        Index("ix_record_due_status", "due_at", "status"),
    )

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    thread_id: Mapped[int | None] = mapped_column(BigInteger)
    kind: Mapped[RecordKind] = mapped_column(Enum(RecordKind, native_enum=False, length=20))
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, native_enum=False, length=20), default=RecordStatus.OPEN
    )
    text: Mapped[str] = mapped_column(Text)
    source_message_id: Mapped[int] = mapped_column(BigInteger)
    source_excerpt: Mapped[str | None] = mapped_column(String(320))
    source_link: Mapped[str | None] = mapped_column(String(512))
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger)
    owner_label: Mapped[str | None] = mapped_column(String(128))
    created_by_id: Mapped[int] = mapped_column(BigInteger)
    created_by_label: Mapped[str] = mapped_column(String(128))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supersedes_id: Mapped[str | None] = mapped_column(
        ForeignKey("ledger_records.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list[LedgerEvent]] = relationship(
        back_populates="record", cascade="all, delete-orphan", passive_deletes=True
    )


class LedgerEvent(Base):
    __tablename__ = "ledger_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_records.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32))
    actor_user_id: Mapped[int] = mapped_column(BigInteger)
    actor_label: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped[LedgerRecord] = relationship(back_populates="events")
