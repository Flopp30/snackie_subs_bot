"""
start handler
"""
from aiogram import types
from aiogram.enums import ParseMode
from sqlalchemy.orm import sessionmaker

from bot.db.crud import user_crud
from bot.structure.keyboards import START_BOARD, AFTER_PAYMENT_REDIRECT_BOARD
from bot.text_for_messages import TEXT_GREETING, TEXT_MAIN_FOR_IS_ACTIVE_USER
from bot.utils import get_beautiful_sub_date


async def start(
        message: types.Message,
        get_async_session: sessionmaker,
) -> None:

    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=message.from_user.id, session=session)

    if not user.is_active:
        await message.answer(
            TEXT_GREETING,
            parse_mode=ParseMode.HTML,
            reply_markup=START_BOARD,
        )
    else:
        sub_date_text = await get_beautiful_sub_date(first_sub_date=user.first_sub_date)
        await message.answer(
            TEXT_MAIN_FOR_IS_ACTIVE_USER.format(
                first_sub_date=user.first_sub_date.strftime('%d.%m.%Y'),
                sub_humanize_name=user.subscription.humanize_name,
                unsub_date=user.unsubscribe_date.strftime('%d.%m.%Y'),
                sub_date_text=sub_date_text,
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=AFTER_PAYMENT_REDIRECT_BOARD,
        )
