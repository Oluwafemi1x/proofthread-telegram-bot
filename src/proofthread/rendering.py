from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from proofthread.models import LedgerRecord, RecordKind, RecordStatus

KIND_ICON = {
    RecordKind.DECISION: "🧭",
    RecordKind.ACTION: "✅",
    RecordKind.QUESTION: "❓",
}


def render_record(record: LedgerRecord, *, compact: bool = False) -> str:
    heading = (
        f"{KIND_ICON[record.kind]} <b>{record.kind.value.title()}</b> <code>{record.id}</code>"
    )
    lines = [heading, escape(record.text)]
    if record.owner_label:
        lines.append(f"<b>Owner:</b> {escape(record.owner_label)}")
    if record.due_at:
        lines.append(f"<b>Due:</b> {record.due_at.strftime('%Y-%m-%d %H:%M %Z').strip()}")
    lines.append(f"<b>Status:</b> {record.status.value}")
    if not compact:
        lines.append(f"<b>Captured by:</b> {escape(record.created_by_label)}")
        if record.source_link:
            source_url = escape(record.source_link, quote=True)
            lines.append(f'<a href="{source_url}">Open source message</a>')
    return "\n".join(lines)


def record_keyboard(record: LedgerRecord) -> InlineKeyboardMarkup | None:
    buttons: list[InlineKeyboardButton] = []
    if record.status is RecordStatus.OPEN and record.kind is RecordKind.ACTION:
        buttons.append(
            InlineKeyboardButton(text="Mark completed", callback_data=f"pt:completed:{record.id}")
        )
    if record.status is RecordStatus.OPEN and record.kind is RecordKind.QUESTION:
        buttons.append(
            InlineKeyboardButton(text="Mark resolved", callback_data=f"pt:resolved:{record.id}")
        )
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def render_digest(records: list[LedgerRecord]) -> str:
    if not records:
        return "🎉 <b>Nothing is waiting for follow-up.</b>"
    groups = {
        RecordKind.ACTION: [record for record in records if record.kind is RecordKind.ACTION],
        RecordKind.QUESTION: [record for record in records if record.kind is RecordKind.QUESTION],
        RecordKind.DECISION: [record for record in records if record.kind is RecordKind.DECISION],
    }
    lines = ["📌 <b>ProofThread follow-up digest</b>"]
    for kind in (RecordKind.ACTION, RecordKind.QUESTION, RecordKind.DECISION):
        items = groups[kind]
        if not items:
            continue
        lines.append(f"\n{KIND_ICON[kind]} <b>{kind.value.title()}s</b>")
        for item in items[:10]:
            owner = f" · {escape(item.owner_label)}" if item.owner_label else ""
            due = f" · due {item.due_at:%Y-%m-%d}" if item.due_at else ""
            source = ""
            if item.source_link:
                source_url = escape(item.source_link, quote=True)
                source = f' · <a href="{source_url}">source</a>'
            lines.append(f"• <code>{item.id}</code> {escape(item.text[:160])}{owner}{due}{source}")
    return "\n".join(lines)
