from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from proofthread.config import Settings, get_settings
from proofthread.database import create_engine_and_session, upgrade_database
from proofthread.handlers.ledger import create_ledger_router
from proofthread.logging import configure_logging
from proofthread.reminders import send_due_reminders
from proofthread.service import LedgerService

COMMANDS = [
    BotCommand(command="help", description="Show commands"),
    BotCommand(command="decision", description="Capture a decision"),
    BotCommand(command="action", description="Capture an owned action"),
    BotCommand(command="question", description="Capture an unanswered question"),
    BotCommand(command="open", description="Show open follow-ups"),
    BotCommand(command="ledger", description="Show recent ledger records"),
    BotCommand(command="mine", description="Show my assigned actions"),
    BotCommand(command="digest", description="Build a follow-up digest"),
    BotCommand(command="privacy", description="Explain data collection"),
]


def build_runtime(settings: Settings):
    engine, sessions = create_engine_and_session(settings.database_url)
    service = LedgerService(sessions, settings.default_timezone)
    bot = Bot(settings.telegram_bot_token.get_secret_value())
    dispatcher = Dispatcher()
    dispatcher.include_router(create_ledger_router(service))
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        send_due_reminders,
        "interval",
        seconds=settings.reminder_interval_seconds,
        kwargs={
            "bot": bot,
            "service": service,
            "window_minutes": settings.reminder_window_minutes,
        },
        max_instances=1,
        coalesce=True,
    )
    return engine, service, bot, dispatcher, scheduler


async def run_polling(settings: Settings) -> None:
    engine, _service, bot, dispatcher, scheduler = build_runtime(settings)
    if settings.auto_migrate:
        await upgrade_database(settings.database_url)
    await bot.set_my_commands(COMMANDS)
    await bot.delete_webhook(drop_pending_updates=False)
    scheduler.start()
    structlog.get_logger().info("proofthread_started", mode="polling")
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()


def run_webhook(settings: Settings) -> None:
    engine, _service, bot, dispatcher, scheduler = build_runtime(settings)
    application = web.Application()

    async def startup(_app: web.Application) -> None:
        if settings.auto_migrate:
            await upgrade_database(settings.database_url)
        await bot.set_my_commands(COMMANDS)
        await bot.set_webhook(
            f"{settings.webhook_base_url.rstrip('/')}{settings.webhook_path}",
            secret_token=settings.webhook_secret.get_secret_value(),
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        scheduler.start()
        structlog.get_logger().info("proofthread_started", mode="webhook")

    async def shutdown(_app: web.Application) -> None:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        await engine.dispose()

    application.on_startup.append(startup)
    application.on_shutdown.append(shutdown)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.webhook_secret.get_secret_value(),
    ).register(application, path=settings.webhook_path)
    setup_application(application, dispatcher, bot=bot)
    web.run_app(application, host=settings.web_host, port=settings.web_port)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.mode == "webhook":
        run_webhook(settings)
    else:
        asyncio.run(run_polling(settings))


if __name__ == "__main__":
    main()
