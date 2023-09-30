"""
start handler
"""
from aiogram import types
from aiogram.enums import ParseMode
from sqlalchemy.orm import sessionmaker

from bot.db.crud import user_crud, sales_crud
from bot.settings import ADMIN_TG_ID, SECOND_ADMIN_TG, greetings_photo
from bot.structure.keyboards import START_BOARD, AFTER_PAYMENT_REDIRECT_BOARD
from bot.structure.keyboards.admin_board import ADMIN_BOARD
from bot.text_for_messages import TEXT_GREETING, TEXT_MAIN_FOR_IS_ACTIVE_USER, TEXT_NO_SALE
from bot.utils import get_beautiful_sub_date


async def start(
        message: types.Message,
        get_async_session: sessionmaker,
        user_id: int = None,
) -> None:
    """
        Start handler.
    """
    if user_id is None:  # using for redirect to start from other handlers
        user_id = message.from_user.id
    await message.answer_photo(
        photo=greetings_photo,
        caption=TEXT_GREETING,
        parse_mode=ParseMode.HTML,
        reply_markup=START_BOARD,
    )

    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=user_id, session=session)

        if user.is_active:

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

        else:
            is_a_sale_now = await sales_crud.is_a_sale_now(session=session)
            if bool(user.first_sub_date) or is_a_sale_now:
                await message.answer(
                    TEXT_GREETING,
                    parse_mode=ParseMode.HTML,
                    reply_markup=START_BOARD,
                )
            else:
                await message.answer(
                    text=TEXT_NO_SALE,
                )

        if user.id in (int(SECOND_ADMIN_TG), int(ADMIN_TG_ID)):
            await message.answer(
                text="Административная часть",
                reply_markup=ADMIN_BOARD,
            )
