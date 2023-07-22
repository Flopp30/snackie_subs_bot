import asyncio
import datetime
import json

from aiogram import types
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import sessionmaker
from yookassa import Payment as YooPayment

from bot.db.crud import payment_crud, user_crud
from bot.settings import (
    INTERVAL_FOR_CHECKING_PAYMENT_SEC,
    TOTAL_AWAIT_PAYMENT_SEC,
)
from bot.structure.keyboards import get_payment_types_board
from bot.text_for_messages import (
    TEXT_OUT_OF_TIME_FOR_PAYMENT,
    TEXT_PAYMENT_ERROR, TEXT_SUCCESSFUL_AUTO_PAYMENT, TEXT_UNSUCCESSFUL_AUTO_PAYMENT
)
from bot.utils.apsched_utils import (
    unban_user_in_owned_bots,
    send_confirm_message,
    notification_one_day_after_unsuccessful_payment, check_auto_payment, ban_user_in_owned_bots,
)
from bot.utils.utils import get_auto_payment


async def payment_process(
        payment: dict,
        message: types.Message,
        get_async_session: sessionmaker,
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

    async with get_async_session() as session:
        if checked_payment.get('status') == 'succeeded':
            sub_id = int(checked_payment.get("metadata", dict()).get("sub_id", 0))
            sub_period = int(checked_payment.get("metadata", dict()).get("sub_period", 0))
            await send_confirm_message(sub_period=sub_period, message=message, checked_payment=checked_payment)
            await payment_crud.create_payment(
                status=checked_payment.get('status'),
                payment_amount=payment_amount,
                verified_payment_id=checked_payment.get("id"),
                session=session,
                user_id=user_id,
            )
            await unban_user_in_owned_bots(message=message, user_id=user_id, bot=bot)
            await user_crud.set_subscribe(
                user_id=user_id,
                sub_id=sub_id,
                session=session,
                first_time=True,
            )
        else:
            apscheduler.add_job(
                notification_one_day_after_unsuccessful_payment,
                trigger=DateTrigger(run_date=datetime.datetime.now() + datetime.timedelta(days=1)),
                kwargs={
                    "bot": bot,
                    "user_id": user_id,
                    "get_async_session": get_async_session,
                    "apscheduler": apscheduler,
                }
            )

            if time_breaker >= TOTAL_AWAIT_PAYMENT_SEC:
                await message.answer(TEXT_OUT_OF_TIME_FOR_PAYMENT)
            else:
                await payment_crud.create_payment(
                    status=checked_payment.get('status'),
                    payment_amount=payment_amount,
                    verified_payment_id=checked_payment.get("payment_method", {}).get("id"),
                    session=session,
                    user_id=user_id,
                )

                await message.answer(
                    TEXT_PAYMENT_ERROR,
                    reply_markup=(await get_payment_types_board(session=session))
                )


async def check_auto_payment_daily(get_async_session: sessionmaker, bot):
    async with get_async_session() as session:
        users = await user_crud.get_expired_sub_user(session=session)
        for user in users:
            if user.verified_payment_id and user.is_accepted_for_auto_payment:
                payment = get_auto_payment(user.subscription, user)
                payment_id = payment.get("id", None)

                if (checked_payment := await check_auto_payment(payment_id)):
                    await bot.send_message(
                        user.id,
                        text=TEXT_SUCCESSFUL_AUTO_PAYMENT.format(
                            payment_name=user.subscription.payment_name
                        )
                    )
                    await payment_crud.create_payment(
                        user_id=user.id,
                        status=payment.get('status'),
                        payment_amount=float(checked_payment.get("amount", dict()).get("value")),
                        session=session,
                    )
                    await user_crud.set_subscribe(
                        subscription=user.subscription,
                        user=user,
                        session=session,
                        first_time=False,
                    )
            else:
                await user_crud.unsubscribe(
                    user=user,
                    session=session
                )
                await ban_user_in_owned_bots(user=user, bot=bot)
                await bot.send_message(
                    user.id,
                    text=TEXT_UNSUCCESSFUL_AUTO_PAYMENT,
                    reply_markup=(await get_payment_types_board(session=session))
                )

            await session.commit()
