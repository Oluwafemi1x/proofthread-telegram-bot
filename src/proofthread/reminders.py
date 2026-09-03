import structlog
from aiogram import Bot
from aiogram.enums import ParseMode

from proofthread.rendering import render_record
from proofthread.service import LedgerService

logger = structlog.get_logger()


async def send_due_reminders(bot: Bot, service: LedgerService, window_minutes: int) -> None:
    records = await service.due_reminders(window_minutes)
    for record in records:
        try:
            await bot.send_message(
                record.telegram_chat_id,
                "⏰ <b>Action due soon</b>\n\n" + render_record(record),
                parse_mode=ParseMode.HTML,
                message_thread_id=record.thread_id,
                disable_web_page_preview=True,
            )
            await service.mark_reminded(record.id)
        except Exception:
            logger.exception("reminder_delivery_failed", record_id=record.id)
