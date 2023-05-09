"""
Main
"""
import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.db import (
    create_async_engine,
    get_session_maker,
)
from bot.handlers import register_user_commands, BOT_COMMANDS_INFO
from bot.settings import TG_BOT_KEY, POSTGRES_URL, logger
from bot.utils import apsched
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def async_main() -> None:
    # init dispatcher and bot
    bot = Bot(token=TG_BOT_KEY)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    # handlers
    commands_for_bot = []
    for cmd in BOT_COMMANDS_INFO:
        commands_for_bot.append(BotCommand(command=cmd[0], description=cmd[1]))
    await bot.set_my_commands(commands_for_bot)
    register_user_commands(dp)
    # db
    async_engine = create_async_engine(POSTGRES_URL)
    session_maker = await get_session_maker(async_engine)

    # periodic tasks
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        apsched.kick_inactive_users,
        trigger="cron",
        hour=datetime.now().hour - 1,
        minute=datetime.now().minute + 2,
        start_date=datetime.now() - timedelta(days=1),
        kwargs={
            "bot": bot,
            "session": session_maker,
        }
    )
    scheduler.add_job(
        apsched.mark_unsubscribed_user_as_inactive,
        trigger="cron",
        hour=datetime.now().hour - 1,
        minute=datetime.now().minute + 1,
        start_date=datetime.now() - timedelta(days=1),
        kwargs={
            "session": session_maker,
        }
    )
    scheduler.start()
    await dp.start_polling(bot, session_maker=session_maker)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        logger.debug("Bot stopped")


if __name__ == "__main__":
    main()
