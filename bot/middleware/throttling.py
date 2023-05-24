from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import TelegramObject, Message

from bot.text_for_messages import TEXT_SPAM_MESSAGE


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, storage: RedisStorage):
        self.storage = storage

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any],
                       ) -> Any:
        user = f'user{event.from_user.id}'

        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user.decode()) == 1:
                await self.storage.redis.set(name=user, value=0, ex=3)
                return await event.answer(TEXT_SPAM_MESSAGE)
            return
        await self.storage.redis.set(name=user, value=1, ex=3)

        return await handler(event, data)
