import asyncio
import datetime
import json

import aiohttp
from aiogram import types
from sqlalchemy.orm import sessionmaker
from yookassa import Payment as YooPayment

from bot.db import (
    User,
    unsubscribe_user,
    create_payment,
    set_subscribe_after_payment, get_object
)
from bot.settings import (
    OWNED_BOTS,
    HEADERS,
    ADMIN_TG_ID,
    logger,
    INTERVAL_FOR_CHECKING_PAYMENT_SEC
)
from bot.structure.keyboards import AFTER_PAYMENT_REDIRECT_BOARD, PAYMENT_TYPE_BOARD, START_BOARD
from bot.text_for_messages import (
    TEXT_UNBAN_ERROR_USER,
    TEXT_UNBAN_ERROR_ADMIN,
    TEXT_PAYMENT_INFO,
    TEXT_SUCCESSFUL_PAYMENT,
    TEXT_SUCCESSFUL_AUTO_PAYMENT,
    TEXT_UNSUCCESSFUL_AUTO_PAYMENT,
    TEXT_NOTIFICATION_ONE_DAY_AFTER_UNSUCCESSFUL_PAYMENT,
    TEXT_NOTIFICATION_FIVE_DAYS_AFTER_UNSUCCESSFUL_PAYMENT,
)
from bot.utils.utils import get_auto_payment


async def auto_payment_process(session: sessionmaker, user: User, bot):
    if user.verified_payment_id and user.is_accepted_for_auto_payment:
        payment = await get_auto_payment(user.subscription, user)
        payment_id = payment.get("id", None)
        if await check_auto_payment(payment_id):
            await set_subscribe_after_payment(
                verified_payment_id=payment_id,
                subscription=user.subscription,
                user=user,
                session=session,
                first_time=False,
            )
            await bot.send_message(
                user.id,
                text=TEXT_SUCCESSFUL_AUTO_PAYMENT.format(
                    payment_name=user.subscription.payment_name,
                    unsubscribe_date=user.unsubscribe_date.strftime('%d.%m.%Y')
                )
            )
            await create_payment(
                user_id=user.id,
                status=payment.get('status'),
                payment_amount=float(payment.get("amount", dict()).get("value")),
                verified_payment_id=payment.get("id"),
                session=session,
            )
        else:
            await unsubscribe_user(user=user, session=session)
            await ban_user_in_owned_bots(user=user, bot=bot)
            await bot.send_message(
                user.id,
                text=TEXT_UNSUCCESSFUL_AUTO_PAYMENT,
                reply_markup=PAYMENT_TYPE_BOARD
            )


async def ban_user_in_owned_bots(user: User, bot):
    for owned_bot in OWNED_BOTS:
        ban_url = owned_bot.get_ban_url(user_id=user.id)
        async with aiohttp.ClientSession() as aio_session:
            response = await aio_session.get(ban_url, headers=HEADERS)
            status_code = json.loads(await response.text()).get("code")
            if status_code != 0:
                await bot.send_message(ADMIN_TG_ID,
                                       f"Проблема с баном пользователя: {user} в боте {owned_bot.name}")
                logger.error(f"Something went wrong. Can't banned user {user} in bot {owned_bot.name}")
            else:
                logger.info(f"User {user} was banned in bot {owned_bot.name}")


async def unban_user_in_owned_bots(message: types.Message, user_id: int, bot):
    for owned_bot in OWNED_BOTS:
        unban_url = owned_bot.get_unban_url(user_id=user_id)
        async with aiohttp.ClientSession() as aio_session:
            response = await aio_session.get(unban_url, headers=HEADERS)
            status_code = json.loads(await response.text()).get("code", "1")
            if status_code != 0:
                await asyncio.sleep(0.5)
                await message.answer(text=TEXT_UNBAN_ERROR_USER.format(user_id=user_id))
                await bot.send_message(
                    ADMIN_TG_ID,
                    text=TEXT_UNBAN_ERROR_ADMIN.format(
                        bot_name=owned_bot.name,
                        user_id=user_id
                    )
                )
                logger.error(f"Something went wrong. Can't banned user {user_id} in bot {owned_bot.name}")
            else:
                logger.info(f"User {user_id} was unbanned in bot {owned_bot.name}")
    await asyncio.sleep(0.5)


async def send_confirm_message(sub_period, checked_payment, message):
    currency = checked_payment.get("amount", dict()).get("currency", None)
    value = checked_payment.get("amount", dict()).get("value", None)
    sub_period_text = "1 месяц"
    match sub_period:
        case 1:
            pass
        case 3:
            sub_period_text = "3 месяца"
        case 12:
            sub_period_text = "1 год"
    await message.answer(
        TEXT_PAYMENT_INFO.format(value=value, currency=currency, sub_period_text=sub_period_text)
    )

    await message.answer(text=TEXT_SUCCESSFUL_PAYMENT, reply_markup=AFTER_PAYMENT_REDIRECT_BOARD)


async def check_auto_payment(payment_id):
    payment = json.loads((YooPayment.find_one(payment_id)).json())
    while payment['status'] == 'pending':
        payment = json.loads((YooPayment.find_one(payment_id)).json())
        await asyncio.sleep(INTERVAL_FOR_CHECKING_PAYMENT_SEC)
    if payment['status'] == 'succeeded':
        return True
    else:
        return False


async def notification_one_day_after_unsuccessful_payment(bot, user_id, session, apscheduler):
    user = await get_object(User, id_=user_id, session=session)
    if not user.is_active:
        await bot.send_message(
            user_id,
            text=TEXT_NOTIFICATION_ONE_DAY_AFTER_UNSUCCESSFUL_PAYMENT,
            reply_markup=START_BOARD
        )
        apscheduler.add_job(
            notification_five_days_after_unsuccessful_payment,
            trigger="date",
            run_date=datetime.datetime.now() + datetime.timedelta(days=2),
            kwargs={
                "bot": bot,
                "user_id": user_id,
                "session": session,
            }
        )


async def notification_five_days_after_unsuccessful_payment(bot, user_id, session):
    user = await get_object(User, id_=user_id, session=session)
    if not user.is_active:
        await bot.send_message(
            user_id,
            text=TEXT_NOTIFICATION_FIVE_DAYS_AFTER_UNSUCCESSFUL_PAYMENT,
            reply_markup=START_BOARD
        )
