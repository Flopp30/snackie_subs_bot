import logging

from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.crud import sub_crud
from bot.structure import PaymentTypeStates


async def get_payment_types_board(session: AsyncSession, with_trials: bool = True, with_amount: bool = False):
    subs = await sub_crud.get_multi(session, with_trials=with_trials)
    builder = InlineKeyboardBuilder()

    for sub in subs:
        if not isinstance(sub, dict):
            sub = sub.to_dict()

        if with_amount:
            button_text = f"{sub.get('payment_name')} ({sub.get('payment_amount')} {sub.get('payment_currency')})"
        else:
            button_text = sub.get('payment_name')

        builder.button(
            text=button_text, callback_data=PaymentTypeStates(sub_period=sub.get("sub_period"))
        )
    builder.adjust(1)

    return builder.as_markup()
