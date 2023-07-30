from aiogram import types
from sqlalchemy.orm import sessionmaker
from bot.db.crud import user_crud
from bot.settings import ADMIN_TG_ID
from bot.structure import UnsubStates
from bot.structure.keyboards import UNSUB_BOARD
from bot.text_for_messages import TEXT_UNSUBSCRIPTION_START, TEXT_UNSUB_ERROR_USER, TEXT_UNSUB_ERROR_ADMIN
from bot.utils import get_beautiful_sub_date


async def unsubscription_start(
        message: types.Message,
        get_async_session: sessionmaker,
) -> None:
    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=message.from_user.id, session=session)

    if user.is_accepted_for_auto_payment:
        sub_date_text = await get_beautiful_sub_date(first_sub_date=user.first_sub_date)
        text = TEXT_UNSUBSCRIPTION_START.format(
            unsub_date=user.unsubscribe_date.strftime('%d.%m.%Y'),
            sub_date_text=sub_date_text
        )
        await message.answer(
            text=text,
            reply_markup=UNSUB_BOARD,
        )
    else:
        if user.unsubscribe_date is not None:
            await message.answer(
                text=f"Текущая подписка завершится {user.unsubscribe_date.strftime('%d.%m.%Y')} и "
                     f"автоматически продлеваться не будет",
            )
        else:
            await message.answer(
                text="У тебя нет активных подписок",
            )


async def unsub_process(
        callback_query: types.CallbackQuery,
        get_async_session: sessionmaker,
        callback_data: UnsubStates,
        bot,
):
    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=callback_query.from_user.id, session=session)
        if user:
            if callback_data.answer == "Yes":
                user.is_accepted_for_auto_payment = False
                await user_crud.update(user, {"is_accepted_for_auto_payment": False}, session)
                await callback_query.message.answer(f"Подписка успешно завершена. "
                                                    f"Дата окончания: {user.unsubscribe_date.strftime('%d.%m.%Y')}")
            else:
                await callback_query.message.answer("Рада, что ты решила остаться!")
        else:
            await callback_query.message.answer(TEXT_UNSUB_ERROR_USER.format(user_id=callback_query.from_user.id))
            await bot.send_message(ADMIN_TG_ID, TEXT_UNSUB_ERROR_ADMIN.format(user_id=callback_query.from_user.id))
