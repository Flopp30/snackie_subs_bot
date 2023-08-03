import asyncio
import datetime
import logging

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import sessionmaker

from bot.db.crud import user_crud
from bot.db.crud.task import task_crud
from bot.handlers.start import start
from bot.structure import PaymentTypeStates
from bot.structure.keyboards import get_payment_types_board, get_payment_board
from bot.text_for_messages import TEXT_INVOICE
from bot.utils import get_tariffs_text, get_yoo_payment
from bot.utils.apsched import payment_process


async def subscription_start(
        callback_query: types.CallbackQuery,
        get_async_session: sessionmaker,
        state: FSMContext,
) -> None:
    async with get_async_session() as session:
        user = await user_crud.get_by_id(user_pk=callback_query.from_user.id, session=session)
        if not user.is_active:
            text = await get_tariffs_text(session=session, state=state, with_trials=not bool(user.first_sub_date))
            await callback_query.message.answer(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=(await get_payment_types_board(
                    session=session,
                    with_trials=not bool(user.first_sub_date)
                )),
            )
        else:
            return await start(message=callback_query.message, get_async_session=get_async_session)


async def send_subscribe_invoice(
        callback_query: types.CallbackQuery,
        callback_data: PaymentTypeStates,
        state: FSMContext,
        get_async_session: sessionmaker,
        apscheduler: AsyncIOScheduler,
        bot,
) -> None:
    state_data: dict = await state.get_data()
    subscriptions: list = state_data.get("subscriptions", "")

    current_sub: dict | None = None

    for sub in subscriptions:
        if sub.get("sub_period") == callback_data.sub_period:
            current_sub = sub
            break

    yoo_payment = await get_yoo_payment(current_sub)

    url = yoo_payment.get("confirmation", dict()).get("confirmation_url", None)

    invoice = await callback_query.message.answer(
        text=TEXT_INVOICE,
        reply_markup=get_payment_board(
            payment_amount=current_sub.get("payment_amount"),
            payment_currency=current_sub.get("payment_currency"),
            url=url
        )
    )
    user_id = callback_query.from_user.id
    job = apscheduler.add_job(
        payment_process,
        kwargs={
            "payment": yoo_payment,
            "message": callback_query.message,
            "get_async_session": get_async_session,
            "user_id": user_id,
            "invoice_for_delete": invoice,
            "bot": bot,
            "apscheduler": apscheduler,
        }
    )
    async with get_async_session() as session:
        tasks = await task_crud.get_active_payment_process_tasks_by_user_id(user_pk=user_id, session=session)
    async with get_async_session() as session:
        await task_crud.create({
            'message_id': invoice.message_id,
            'status': 'active',
            'type': 'payment_process',
            'user_id': user_id,
            'job_id': job.id,
        }, session=session)
    await asyncio.sleep(0.5)
    await asyncio.gather(*[process_task(task, job, bot, user_id, get_async_session) for task in tasks])


async def process_task(task, job, bot, user_id, get_async_session):
    async with get_async_session() as session:
        if task.job_id != job.id:
            await task_crud.update(task, {'status': 'canceled'}, session=session)
            await bot.delete_message(user_id, task.message_id)
