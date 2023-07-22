from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.crud import sub_crud
from bot.structure import PaymentTypeStates


async def get_payment_types_board(session: AsyncSession):
    subs = await sub_crud.get_multi(session)
    builder = InlineKeyboardBuilder()

    for sub in subs:
        if not isinstance(sub, dict):
            sub = sub.to_dict()
        builder.button(
            text=sub.get("payment_name"), callback_data=PaymentTypeStates(sub_period=sub.get("sub_period"))
        )
    builder.adjust(1)

    return builder.as_markup()
