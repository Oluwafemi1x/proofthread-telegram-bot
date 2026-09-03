from __future__ import annotations

import json
from datetime import UTC, datetime
from html import escape

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus, ChatType, ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, CallbackQuery, Message, User

from proofthread.links import telegram_message_link
from proofthread.models import RecordKind, RecordStatus
from proofthread.parsing import ActionSyntaxError, parse_action_args
from proofthread.rendering import record_keyboard, render_digest, render_record
from proofthread.service import Actor, InvalidTransition, LedgerService, RecordNotFound

HELP_TEXT = """<b>ProofThread — accountable group memory</b>

Reply to a message, then use:
<code>/decision Final wording</code>
<code>/action 2026-09-10 @owner Ship the release</code>
<code>/action - me Review the pull request</code>
<code>/question What is blocking deployment?</code>

Review and follow up:
<code>/ledger</code> — recent records
<code>/open</code> — open actions and questions
<code>/mine</code> — actions assigned directly to you
<code>/digest</code> — follow-up summary
<code>/complete ID</code> — complete an action
<code>/resolve ID</code> — resolve a question
<code>/cancel ID</code> — cancel your record
<code>/supersede ID New decision</code> — replace a decision

Admin tools:
<code>/settimezone Africa/Lagos</code>
<code>/export</code>
<code>/forget ID</code>

ProofThread stores only explicit ledger records and a short source excerpt—not the entire chat."""


def user_label(user: User) -> str:
    return f"@{user.username}" if user.username else user.full_name


def actor(user: User) -> Actor:
    return Actor(user_id=user.id, label=user_label(user))


def source_from(message: Message) -> Message:
    return message.reply_to_message or message


def source_excerpt(message: Message) -> str | None:
    value = message.text or message.caption
    return " ".join(value.split())[:320] if value else None


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}


def create_ledger_router(service: LedgerService) -> Router:
    router = Router(name="ledger")

    async def require_group(message: Message) -> bool:
        if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await message.answer("Add ProofThread to a group to create a shared ledger.")
            return False
        await service.ensure_chat(message.chat.id, message.chat.title)
        return True

    async def capture(
        message: Message,
        kind: RecordKind,
        text: str,
        *,
        owner_user_id: int | None = None,
        owner_label: str | None = None,
        due_at: datetime | None = None,
        supersedes_id: str | None = None,
    ) -> None:
        source = source_from(message)
        record = await service.create_record(
            chat_id=message.chat.id,
            thread_id=message.message_thread_id,
            kind=kind,
            text=text,
            source_message_id=source.message_id,
            source_excerpt=source_excerpt(source),
            source_link=telegram_message_link(
                message.chat.id, message.chat.username, source.message_id
            ),
            actor=actor(message.from_user),
            owner_user_id=owner_user_id,
            owner_label=owner_label,
            due_at=due_at,
            supersedes_id=supersedes_id,
        )
        await message.answer(
            render_record(record),
            parse_mode=ParseMode.HTML,
            reply_markup=record_keyboard(record),
            disable_web_page_preview=True,
        )

    @router.message(Command("start", "help"))
    async def help_command(message: Message) -> None:
        await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)

    @router.message(Command("privacy"))
    async def privacy_command(message: Message) -> None:
        await message.answer(
            "🔐 <b>Privacy by default</b>\n\n"
            "ProofThread records only commands, the ledger text you provide, a short excerpt "
            "of a replied-to source, identifiers needed for ownership, and state-change history. "
            "It does not need to archive every group message. Admins can export or delete records.",
            parse_mode=ParseMode.HTML,
        )

    @router.message(Command("decision"))
    async def decision_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        text = (command.args or "").strip()
        if not text and message.reply_to_message:
            text = source_excerpt(message.reply_to_message) or ""
        if len(text) < 3:
            await message.answer(
                "Reply to a message with <code>/decision Final wording</code>.",
                parse_mode=ParseMode.HTML,
            )
            return
        await capture(message, RecordKind.DECISION, text)

    @router.message(Command("question"))
    async def question_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        text = (command.args or "").strip()
        if not text and message.reply_to_message:
            text = source_excerpt(message.reply_to_message) or ""
        if len(text) < 3:
            await message.answer(
                "Use <code>/question What needs an answer?</code>.",
                parse_mode=ParseMode.HTML,
            )
            return
        await capture(message, RecordKind.QUESTION, text)

    @router.message(Command("action"))
    async def action_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        try:
            parsed = parse_action_args(command.args, await service.chat_timezone(message.chat.id))
        except ActionSyntaxError as exc:
            await message.answer(
                f"{escape(str(exc))}\n\n"
                "Example: <code>/action 2026-09-10 @femi Publish the release</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        owner_user_id = None
        owner_label = parsed.owner_label
        if owner_label == "me":
            owner_user_id = message.from_user.id
            owner_label = user_label(message.from_user)
        elif owner_label and message.from_user.username:
            if owner_label.casefold() == f"@{message.from_user.username}".casefold():
                owner_user_id = message.from_user.id
        replied_user = message.reply_to_message.from_user if message.reply_to_message else None
        if owner_label and replied_user and replied_user.username:
            if owner_label.casefold() == f"@{replied_user.username}".casefold():
                owner_user_id = replied_user.id
        await capture(
            message,
            RecordKind.ACTION,
            parsed.text,
            owner_user_id=owner_user_id,
            owner_label=owner_label,
            due_at=parsed.due_at,
        )

    @router.message(Command("ledger"))
    async def ledger_command(message: Message) -> None:
        if not await require_group(message):
            return
        records = await service.list_records(message.chat.id, limit=15)
        if not records:
            await message.answer(
                "The ledger is empty. Reply to a message with /decision, /action or /question."
            )
            return
        await message.answer(
            "\n\n".join(render_record(item, compact=True) for item in records),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    @router.message(Command("open", "digest"))
    async def open_command(message: Message) -> None:
        if not await require_group(message):
            return
        records = await service.list_records(
            message.chat.id,
            kinds=[RecordKind.ACTION, RecordKind.QUESTION],
            statuses=[RecordStatus.OPEN],
            limit=50,
        )
        await message.answer(
            render_digest(records), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    @router.message(Command("mine"))
    async def mine_command(message: Message) -> None:
        if not await require_group(message):
            return
        records = await service.list_records(
            message.chat.id,
            kinds=[RecordKind.ACTION],
            statuses=[RecordStatus.OPEN],
            owner_user_id=message.from_user.id,
            limit=30,
        )
        await message.answer(
            render_digest(records), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    async def transition_from_command(
        message: Message, command: CommandObject, target: RecordStatus
    ) -> None:
        if not await require_group(message):
            return
        record_id = (command.args or "").strip()
        if not record_id:
            await message.answer(f"Use /{target.value} RECORD_ID")
            return
        try:
            record = await service.get_record(message.chat.id, record_id)
            permitted = (
                record.created_by_id == message.from_user.id
                or record.owner_user_id == message.from_user.id
            )
            if not permitted:
                permitted = await is_admin(message.bot, message.chat.id, message.from_user.id)
            if not permitted:
                await message.answer(
                    "Only the creator, assigned owner, or a group administrator can do that."
                )
                return
            record = await service.transition(
                chat_id=message.chat.id,
                record_id=record_id,
                actor=actor(message.from_user),
                target=target,
            )
        except (RecordNotFound, InvalidTransition) as exc:
            await message.answer(escape(str(exc)))
            return
        await message.answer(render_record(record), parse_mode=ParseMode.HTML)

    @router.message(Command("complete"))
    async def complete_command(message: Message, command: CommandObject) -> None:
        await transition_from_command(message, command, RecordStatus.COMPLETED)

    @router.message(Command("resolve"))
    async def resolve_command(message: Message, command: CommandObject) -> None:
        await transition_from_command(message, command, RecordStatus.RESOLVED)

    @router.message(Command("cancel"))
    async def cancel_command(message: Message, command: CommandObject) -> None:
        await transition_from_command(message, command, RecordStatus.CANCELLED)

    @router.message(Command("supersede"))
    async def supersede_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        parts = (command.args or "").split(maxsplit=1)
        if len(parts) != 2:
            await message.answer(
                "Use: <code>/supersede DECISION_ID New decision</code>",
                parse_mode=ParseMode.HTML,
            )
            return
        old_id, text = parts
        try:
            old = await service.get_record(message.chat.id, old_id)
            if old.created_by_id != message.from_user.id and not await is_admin(
                message.bot, message.chat.id, message.from_user.id
            ):
                await message.answer(
                    "Only the decision creator or a group administrator can supersede it."
                )
                return
            await capture(
                message,
                RecordKind.DECISION,
                text,
                supersedes_id=old.id,
            )
        except (RecordNotFound, InvalidTransition) as exc:
            await message.answer(escape(str(exc)))

    @router.callback_query(F.data.startswith("pt:"))
    async def record_callback(callback: CallbackQuery) -> None:
        if not callback.message or not callback.data:
            await callback.answer()
            return
        _, target_value, record_id = callback.data.split(":", maxsplit=2)
        try:
            target = RecordStatus(target_value)
            record = await service.get_record(callback.message.chat.id, record_id)
            permitted = (
                record.created_by_id == callback.from_user.id
                or record.owner_user_id == callback.from_user.id
            )
            if not permitted:
                permitted = await is_admin(
                    callback.bot, callback.message.chat.id, callback.from_user.id
                )
            if not permitted:
                await callback.answer("You are not allowed to close this record.", show_alert=True)
                return
            record = await service.transition(
                chat_id=callback.message.chat.id,
                record_id=record_id,
                actor=actor(callback.from_user),
                target=target,
            )
            await callback.message.edit_text(
                render_record(record), parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            await callback.answer("Updated")
        except (ValueError, RecordNotFound, InvalidTransition) as exc:
            await callback.answer(str(exc), show_alert=True)

    @router.message(Command("settimezone"))
    async def timezone_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        if not await is_admin(message.bot, message.chat.id, message.from_user.id):
            await message.answer("Only a group administrator can change the timezone.")
            return
        value = (command.args or "").strip()
        try:
            chat = await service.set_chat_timezone(message.chat.id, value)
        except ValueError as exc:
            await message.answer(escape(str(exc)))
            return
        await message.answer(
            f"Timezone updated to <code>{escape(chat.timezone)}</code>.",
            parse_mode=ParseMode.HTML,
        )

    @router.message(Command("export"))
    async def export_command(message: Message) -> None:
        if not await require_group(message):
            return
        if not await is_admin(message.bot, message.chat.id, message.from_user.id):
            await message.answer("Only a group administrator can export the ledger.")
            return
        payload = {
            "schema": "proofthread.export.v1",
            "exported_at": datetime.now(UTC).isoformat(),
            "chat_id": message.chat.id,
            "records": await service.export_records(message.chat.id),
        }
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        await message.answer_document(
            BufferedInputFile(data, filename=f"proofthread-{message.chat.id}.json"),
            caption="ProofThread ledger export",
        )

    @router.message(Command("forget"))
    async def forget_command(message: Message, command: CommandObject) -> None:
        if not await require_group(message):
            return
        record_id = (command.args or "").strip()
        try:
            record = await service.get_record(message.chat.id, record_id)
            permitted = record.created_by_id == message.from_user.id or await is_admin(
                message.bot, message.chat.id, message.from_user.id
            )
            if not permitted:
                await message.answer(
                    "Only the creator or a group administrator can delete that record."
                )
                return
            deleted = await service.delete_record(message.chat.id, record.id)
        except RecordNotFound as exc:
            await message.answer(escape(str(exc)))
            return
        await message.answer(
            f"Deleted ledger record <code>{deleted}</code>.",
            parse_mode=ParseMode.HTML,
        )

    return router
