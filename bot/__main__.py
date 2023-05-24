"""
Main
"""
import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from redis.asyncio.client import Redis
from yookassa import Configuration

from bot.db import (
    create_async_engine,
    get_session_maker,
)
from bot.handlers import register_user_commands, BOT_COMMANDS_INFO
from bot.middleware.apscheduler import SchedulerMiddleware
from bot.middleware.throttling import ThrottlingMiddleware
from bot.settings import TG_BOT_KEY, POSTGRES_URL, logger, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from bot.utils import apsched
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def async_main() -> None:
    # yookassa connect
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY
    # init dispatcher and bot
    bot = Bot(token=TG_BOT_KEY)
    redis = Redis()
    storage = RedisStorage(redis)
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
        apsched.check_auto_payment_daily,
        trigger="cron",
        start_date=datetime.now(),
        hour=datetime.now().hour,
        minute=datetime.now().minute,
        kwargs={
            "session": session_maker,
            "bot": bot,
        }
    )

    scheduler.start()

    dp.update.middleware.register(SchedulerMiddleware(scheduler))
    dp.message.middleware.register(ThrottlingMiddleware(storage))
    await dp.start_polling(bot, session_maker=session_maker)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        logger.debug("Bot stopped")


if __name__ == "__main__":
    main()
