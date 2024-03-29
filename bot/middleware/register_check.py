"""
Create new user after start chatting
"""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.db.crud import user_crud


class RegisterCheck(BaseMiddleware):
    """
        Check if user is registered
    """
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        get_async_session = data["get_async_session"]
        async with get_async_session() as session:
            user = await user_crud.get_by_attribute(
                attr_name='id',
                attr_value=event.from_user.id,
                session=session,
                is_deleted=False
            )
            if not user:
                await user_crud.create(
                    {
                        'id': event.from_user.id,
                        'username': event.from_user.username
                    },
                    session=session
                )

        return await handler(event, data)
