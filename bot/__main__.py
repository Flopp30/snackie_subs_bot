"""
Main
"""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio.client import Redis
from yookassa import Configuration

from bot.db.engine import get_async_session
from bot.handlers import register_user_commands, BOT_COMMANDS_INFO
from bot.middleware.apscheduler import SchedulerMiddleware
from bot.middleware.throttling import ThrottlingMiddleware
from bot.settings import TG_BOT_KEY, logger, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from bot.utils import apsched


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

    # periodic tasks
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        apsched.check_auto_payment_daily,
        trigger=IntervalTrigger(seconds=5),
        kwargs={
            "get_async_session": get_async_session,
            "bot": bot,
        }
    )

    scheduler.start()

    dp.update.middleware.register(SchedulerMiddleware(scheduler))
    dp.message.middleware.register(ThrottlingMiddleware(storage))
    await dp.start_polling(bot, get_async_session=get_async_session)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        logger.debug("Bot stopped")


if __name__ == "__main__":
    main()
