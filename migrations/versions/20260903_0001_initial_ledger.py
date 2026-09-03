"""Create the ProofThread ledger schema.

Revision ID: 20260903_0001
Revises:
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

record_kind = sa.Enum(
    "DECISION",
    "ACTION",
    "QUESTION",
    name="recordkind",
    native_enum=False,
    length=20,
)
record_status = sa.Enum(
    "OPEN",
    "COMPLETED",
    "RESOLVED",
    "SUPERSEDED",
    "CANCELLED",
    name="recordstatus",
    native_enum=False,
    length=20,
)


def upgrade() -> None:
    op.create_table(
        "chat_settings",
        sa.Column("telegram_chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "ledger_records",
        sa.Column("id", sa.String(length=12), primary_key=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("thread_id", sa.BigInteger(), nullable=True),
        sa.Column("kind", record_kind, nullable=False),
        sa.Column("status", record_status, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_message_id", sa.BigInteger(), nullable=False),
        sa.Column("source_excerpt", sa.String(length=320), nullable=True),
        sa.Column("source_link", sa.String(length=512), nullable=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_label", sa.String(length=128), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_label", sa.String(length=128), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "supersedes_id",
            sa.String(length=12),
            sa.ForeignKey("ledger_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_record_chat_status_kind",
        "ledger_records",
        ["telegram_chat_id", "status", "kind"],
    )
    op.create_index("ix_record_due_status", "ledger_records", ["due_at", "status"])
    op.create_index(
        "ix_ledger_records_telegram_chat_id",
        "ledger_records",
        ["telegram_chat_id"],
    )
    op.create_table(
        "ledger_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "record_id",
            sa.String(length=12),
            sa.ForeignKey("ledger_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_label", sa.String(length=128), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_ledger_events_record_id", "ledger_events", ["record_id"])


def downgrade() -> None:
    op.drop_index("ix_ledger_events_record_id", table_name="ledger_events")
    op.drop_table("ledger_events")
    op.drop_index("ix_ledger_records_telegram_chat_id", table_name="ledger_records")
    op.drop_index("ix_record_due_status", table_name="ledger_records")
    op.drop_index("ix_record_chat_status_kind", table_name="ledger_records")
    op.drop_table("ledger_records")
    op.drop_table("chat_settings")
