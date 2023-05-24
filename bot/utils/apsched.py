import asyncio
import json
import datetime

from aiogram import types
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, selectinload
from yookassa import Payment as YooPayment

from bot.db import (
    User,
    set_subscribe_after_payment,
    create_payment, )
from bot.settings import (
    INTERVAL_FOR_CHECKING_PAYMENT_SEC,
    TOTAL_AWAIT_PAYMENT_SEC,
)
from bot.structure.keyboards import PAYMENT_TYPE_BOARD
from bot.text_for_messages import (
    TEXT_OUT_OF_TIME_FOR_PAYMENT,
    TEXT_PAYMENT_ERROR
)
from bot.utils.apsched_utils import (
    unban_user_in_owned_bots,
    send_confirm_message, auto_payment_process, notification_one_day_after_unsuccessful_payment
)


async def payment_process(
        payment: dict,
        message: types.Message,
        session: sessionmaker,
        user_id: int,
        invoice_for_delete: types.Message,
        bot,
        apscheduler,
):
    payment_id = payment.get("id", None)
    checked_payment = json.loads((YooPayment.find_one(payment_id)).json())
    time_breaker = 0

    while checked_payment['status'] == 'pending' and time_breaker <= TOTAL_AWAIT_PAYMENT_SEC:
        checked_payment = json.loads((YooPayment.find_one(payment_id)).json())
        await asyncio.sleep(INTERVAL_FOR_CHECKING_PAYMENT_SEC)
        time_breaker += INTERVAL_FOR_CHECKING_PAYMENT_SEC

    await invoice_for_delete.delete()
    payment_amount = float(checked_payment.get("amount", dict()).get("value"))

    if time_breaker >= TOTAL_AWAIT_PAYMENT_SEC:
        await message.answer(TEXT_OUT_OF_TIME_FOR_PAYMENT)

    elif checked_payment.get('status') == 'succeeded':
        sub_id = int(checked_payment.get("metadata", dict()).get("sub_id", 0))
        sub_period = int(checked_payment.get("metadata", dict()).get("sub_period", 0))
        await send_confirm_message(sub_period=sub_period, message=message, checked_payment=checked_payment)
        await create_payment(
            user_id=user_id,
            status=checked_payment.get('status'),
            payment_amount=payment_amount,
            verified_payment_id=checked_payment.get("id"),
            session=session,
        )
        await unban_user_in_owned_bots(message=message, user_id=user_id, bot=bot)
        await set_subscribe_after_payment(
            user_id=user_id,
            sub_id=sub_id,
            verified_payment_id=checked_payment.get("id"),
            session=session,
            first_time=True,
        )
    else:
        await create_payment(
            user_id=user_id,
            status=checked_payment.get('status'),
            payment_amount=payment_amount,
            verified_payment_id=checked_payment.get("id"),
            session=session,
        )
        await message.answer(TEXT_PAYMENT_ERROR, reply_markup=PAYMENT_TYPE_BOARD)
        apscheduler.add_job(
            notification_one_day_after_unsuccessful_payment,
            trigger="date",
            run_date=datetime.datetime.now() + datetime.timedelta(days=1),
            kwargs={
                "bot": bot,
                "user_id": user_id,
                "session": session,
                "apscheduler": apscheduler,
            }
        )


async def check_auto_payment_daily(session: sessionmaker, bot):
    async with session() as session_:
        async with session_.begin():
            all_active_user = (await session_.execute(select(User)
                                                      .where(User.is_active)
                                                      .options(selectinload(User.subscription))
                                                      )).scalars()
    for user in all_active_user:
        if user.is_subscribe_ended():
            await auto_payment_process(session=session, user=user, bot=bot)
