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
    """
        Payment process task for apscheduler
    """
    time_breaker = 0
    payment_id = payment.get("id", None)
    checked_payment = json.loads((YooPayment.find_one(payment_id)).json())  # get checked_payment
    payment_amount = float(checked_payment.get("amount", dict()).get("value"))
    async with get_async_session() as session:  # creating payment with status pending
        payment = await payment_crud.create_payment(
            status=checked_payment.get('status'),
            user_id=user_id,
            payment_amount=payment_amount,
            session=session,
        )
    while checked_payment['status'] == 'pending' and time_breaker <= TOTAL_AWAIT_PAYMENT_SEC:  # check payment
        checked_payment = json.loads((YooPayment.find_one(payment_id)).json())
        await asyncio.sleep(INTERVAL_FOR_CHECKING_PAYMENT_SEC)
        time_breaker += INTERVAL_FOR_CHECKING_PAYMENT_SEC  # timebreaker interval (15 min)

    await invoice_for_delete.delete()  # after check (timebreaker interval or changed payment's status)

    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=user_id, session=session)
        if checked_payment.get('status') == 'succeeded':
            sub_id = int(checked_payment.get("metadata", dict()).get("sub_id", 0))  # get sub_id from payment's metadata
            sub_period = int(checked_payment.get("metadata", dict()).get("sub_period", 0))  # sub period

            await send_confirm_message(sub_period=sub_period, message=message, checked_payment=checked_payment)
            await unban_user_in_owned_bots(message=message, user_id=user.id, bot=bot)  # business logic
            await user_crud.set_subscribe(  # subscribe user
                user=user,
                sub_id=sub_id,
                verified_payment_id=checked_payment.get("payment_method", {}).get("id"),
                session=session,
            )

        else:
            apscheduler.add_job(  # add task for one day notification
                # (inside, another task is set - 5 days after the failed payment)

                notification_one_day_after_unsuccessful_payment,
                run_date=datetime.datetime.now() + datetime.timedelta(days=1, hours=3),  # + 3 hours - for server's time
                kwargs={
                    "bot": bot,
                    "user_id": user_id,
                    "get_async_session": get_async_session,
                    "apscheduler": apscheduler,
                }
            )

            if time_breaker >= TOTAL_AWAIT_PAYMENT_SEC:
                await message.answer(TEXT_OUT_OF_TIME_FOR_PAYMENT)  # timeout
            else:
                await message.answer(  # error
                    TEXT_PAYMENT_ERROR,
                    reply_markup=(await get_payment_types_board(
                        session=session,
                        with_trials=not bool(user.first_sub_date)
                    ))
                )

    async with get_async_session() as session:
        # TODO вот тут на 109 строке - хак, чтобы получить payment_id, без этого ошибки
        payment_id = payment.id
        await payment_crud.update(  # update payment status
            payment,
            {
                "status": checked_payment.get('status') if time_breaker <= TOTAL_AWAIT_PAYMENT_SEC else "timeout",
            },
            session=session,
        )
        await payment_crud.mark_canceled_all_unclosed_payments_exclude_current(
            current_payment_id=payment_id, session=session
        )


async def check_auto_payment_daily(get_async_session: sessionmaker, bot: Bot, apscheduler: AsyncIOScheduler):
    """
        Auto payment task daily
    """
    async with get_async_session() as session:
        users = await user_crud.get_expired_sub_users(session=session)

        tasks = [auto_payment_process(user.id, get_async_session, apscheduler, bot) for user in users]

        await asyncio.gather(*tasks)


async def auto_payment_process(
        user_id: int,
        get_async_session: sessionmaker,
        apscheduler: AsyncIOScheduler,
        bot: Bot,
):
    async with get_async_session() as session:
        # TODO вот тут тоже.. У нас по сути выше (128 строка) уже вытащены пользователи,
        #  но из-за сессий приходится каждого отдельно дергать. Мб как-то оптимизировать это дело..
        user = await user_crud.get_by_id(user_id, session=session)
        if user.verified_payment_id and user.is_accepted_for_auto_payment:
            # if we have verified payment id and user not unsubscribed
            payment = get_auto_payment(user.subscription, user)  # get payment
            db_payment = await payment_crud.create_payment(  # create payment with status pending
                user=user,
                status=payment.get('status'),
                payment_amount=float(payment.get("amount", dict()).get("value")),
                session=session,
            )
            if (checked_payment := await check_auto_payment(payment.get("id"))):  # if status succeeded
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
                await payment_crud.update(  # update payment status
                    db_payment,
                    {
                        "status": checked_payment.get('status')
                    },
                    session=session,
                )
            else:  # if payment status not succeeded
                await bot.send_message(
                    user.id,
                    text=TEXT_UNSUCCESSFUL_AUTO_PAYMENT,
                    reply_markup=(await get_payment_types_board(
                        session=session, with_trials=False, with_amount=True
                    ))
                )
                await user_crud.unsubscribe(
                    db_obj=user,
                    session=session
                )
                await ban_user_in_owned_bots(user_id=user.id, bot=bot)
                await payment_crud.update(  # update payment status
                    db_payment,
                    {
                        "status": "canceled"
                    },
                    session=session,
                )
        else:
            if user.subscription.is_trial:  # if user's sub is trial - we don't charge money automatically,
                # but give the opportunity to renew subscription, if necessary
                message_for_deleting = await bot.send_message(
                    user.id,
                    text=TEXT_AFTER_TRIAL,
                    reply_markup=(await get_payment_types_board(
                        session=session, with_trials=False, with_amount=True
                    ))
                )
                apscheduler.add_job(  # but he can renew only with 24 hours -
                    # delete message with payment board after that
                    delete_message_with_payment_board_after_24_hours,
                    trigger=DateTrigger(
                        run_date=datetime.datetime.now() + datetime.timedelta(days=1, hours=3)),
                    kwargs={
                        "message_id": message_for_deleting.message_id,
                        "user_id": user.id,
                        "get_async_session": get_async_session,
                        "bot": bot,
                    }
                )
            else:  # if not sub.is_trial and not is_accepted_for_auto_payment - then the user unsubscribed
                await bot.send_message(
                    user.id,
                    text=TEXT_UNSUBSCRIPTION_SUB_END
                )
            await user_crud.unsubscribe(
                db_obj=user,
                session=session
            )
            await ban_user_in_owned_bots(user_id=user.id, bot=bot)


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
