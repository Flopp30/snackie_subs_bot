import asyncio
import datetime
import json

from aiogram import types, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
    TEXT_PAYMENT_ERROR,
    TEXT_SUCCESSFUL_AUTO_PAYMENT,
    TEXT_UNSUCCESSFUL_AUTO_PAYMENT,
    TEXT_AFTER_TRIAL,
    TEXT_PAYMENT_HAS_NOT_BEEN_RECEIVED,
    TEXT_UNSUBSCRIPTION_SUB_END
)
from bot.utils.apsched_utils import (
    unban_user_in_owned_bots,
    send_confirm_message,
    notification_one_day_after_unsuccessful_payment,
    check_auto_payment,
    ban_user_in_owned_bots,
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
    time_breaker = 0
    payment_id = payment.get("id", None)
    checked_payment = json.loads((YooPayment.find_one(payment_id)).json())
    payment_amount = float(checked_payment.get("amount", dict()).get("value"))
    async with get_async_session() as session:
        payment = await payment_crud.create_payment(
            status=checked_payment.get('status'),
            user_id=user_id,
            payment_amount=payment_amount,
            session=session,
        )
    while checked_payment['status'] == 'pending' and time_breaker <= TOTAL_AWAIT_PAYMENT_SEC:
        checked_payment = json.loads((YooPayment.find_one(payment_id)).json())
        await asyncio.sleep(INTERVAL_FOR_CHECKING_PAYMENT_SEC)
        time_breaker += INTERVAL_FOR_CHECKING_PAYMENT_SEC

    await invoice_for_delete.delete()

    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=user_id, session=session)
        if checked_payment.get('status') == 'succeeded':
            sub_id = int(checked_payment.get("metadata", dict()).get("sub_id", 0))
            sub_period = int(checked_payment.get("metadata", dict()).get("sub_period", 0))
            await send_confirm_message(sub_period=sub_period, message=message, checked_payment=checked_payment)
            await unban_user_in_owned_bots(message=message, user_id=user.id, bot=bot)
            await user_crud.set_subscribe(
                user=user,
                sub_id=sub_id,
                verified_payment_id=checked_payment.get("payment_method", {}).get("id"),
                session=session,
            )
        else:
            apscheduler.add_job(
                notification_one_day_after_unsuccessful_payment,
                run_date=datetime.datetime.now() + datetime.timedelta(days=1, hours=3),
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
                await message.answer(
                    TEXT_PAYMENT_ERROR,
                    reply_markup=(await get_payment_types_board(
                        session=session,
                        with_trials=not bool(user.first_sub_date)
                    ))
                )

    async with get_async_session() as session:
        await payment_crud.update(
            payment,
            {
                "status": checked_payment.get('status'),
            },
            session=session,
        )


async def check_auto_payment_daily(get_async_session: sessionmaker, bot: Bot, apscheduler: AsyncIOScheduler):
    async with get_async_session() as session:
        users = await user_crud.get_expired_sub_users(session=session)
    for user in users:
        async with get_async_session() as session:
            user = await user_crud.get_by_id(user.id, session)
            if user.verified_payment_id and user.is_accepted_for_auto_payment:
                payment = get_auto_payment(user.subscription, user)
                db_payment = await payment_crud.create_payment(
                    user=user,
                    status=payment.get('status'),
                    payment_amount=float(payment.get("amount", dict()).get("value")),
                    session=session,
                )
                if (checked_payment := await check_auto_payment(payment.get("id"))):
                    await bot.send_message(
                        user.id,
                        text=TEXT_SUCCESSFUL_AUTO_PAYMENT.format(
                            payment_name=user.subscription.payment_name
                        )
                    )
                    await user_crud.set_subscribe(
                        verified_payment_id=checked_payment.get("payment_method", {}).get("id"),
                        subscription=user.subscription,
                        user=user,
                        session=session,
                    )
                await payment_crud.update(
                    db_payment,
                    {
                        "status": checked_payment.get('status')
                    },
                    session=session,
                )
            else:
                if user.subscription.is_trial:
                    message_for_deleting = await bot.send_message(
                        user.id,
                        text=TEXT_AFTER_TRIAL,
                        reply_markup=(await get_payment_types_board(
                            session=session, with_trials=False, with_amount=True
                        ))
                    )
                    apscheduler.add_job(
                        delete_message_with_payment_board_after_24_hours,
                        trigger=DateTrigger(
                            run_date=datetime.datetime.now() + datetime.timedelta(days=1, hours=3) + datetime.timedelta(
                                hours=3)),
                        kwargs={
                            "message_id": message_for_deleting.message_id,
                            "user_id": user.id,
                            "get_async_session": get_async_session,
                            "bot": bot,
                        }
                    )
                else:
                    await bot.send_message(
                        user.id,

                        text=TEXT_UNSUCCESSFUL_AUTO_PAYMENT
                        if user.is_accepted_for_auto_payment else TEXT_UNSUBSCRIPTION_SUB_END,

                        reply_markup=(await get_payment_types_board(
                            session=session, with_trials=False, with_amount=True
                        ))
                    )
                await user_crud.unsubscribe(
                    db_obj=user,
                    session=session
                )
                await ban_user_in_owned_bots(user=user, bot=bot)


async def delete_message_with_payment_board_after_24_hours(
        message_id: int,
        user_id: int,
        get_async_session: sessionmaker,
        bot: Bot
):
    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_id, session)
    if not user.is_active:
        await bot.delete_message(user_id, message_id)
        await bot.send_message(user_id, text=TEXT_PAYMENT_HAS_NOT_BEEN_RECEIVED)
