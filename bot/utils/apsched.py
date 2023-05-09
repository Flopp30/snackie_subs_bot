from aiogram import exceptions
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from bot.db import User
from bot.settings import OWNED_CHANNELS, logger


async def kick_inactive_users(session: sessionmaker, bot):
    async with session() as session:
        inactive_users = (await session.execute(select(User).where(User.is_active == False))).scalars()

    for user in inactive_users:
        for chat_id in OWNED_CHANNELS:
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
            except exceptions.TelegramAPIError as e:
                logger.debug(f"Не удалось удалить пользователя <{user}> из чата {chat_id}: {e}")


async def mark_unsubscribed_user_as_inactive(session: sessionmaker):
    async with session() as session:
        async with session.begin():
            active_users = (await session.execute(select(User).where(User.is_active == True))).scalars()

            for user in active_users:
                if user.is_need_to_kick():
                    user.is_active = False
                    user.unsubscribe_date = None
                    session.add(user)

            await session.flush()

