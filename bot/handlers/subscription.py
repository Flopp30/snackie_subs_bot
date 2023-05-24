import datetime

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import sessionmaker

from bot.db import get_object, User
from bot.handlers.start import start
from bot.structure import PaymentTypeStates
from bot.structure.keyboards import PAYMENT_TYPE_BOARD, get_payment_board
from bot.text_for_messages import TEXT_INVOICE
from bot.utils import get_tariffs_text, get_yoo_payment
from bot.utils.apsched import payment_process


async def subscription_start(
        callback_query: types.CallbackQuery,
        session_maker: sessionmaker,
        state: FSMContext,
) -> None:
    user = await get_object(User, id_=callback_query.from_user.id, session=session_maker)
    if not user.is_active:
        text = await get_tariffs_text(session_maker=session_maker, state=state)
        await callback_query.message.answer(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=PAYMENT_TYPE_BOARD,
        )
    else:
        return await start(message=callback_query.message, session_maker=session_maker)


async def send_subscribe_invoice(
        callback_query: types.CallbackQuery,
        callback_data: PaymentTypeStates,
        state: FSMContext,
        session_maker: sessionmaker,
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

    apscheduler.add_job(
        payment_process,
        trigger="date",
        run_date=datetime.datetime.now() - datetime.timedelta(hours=1),
        kwargs={
            "payment": yoo_payment,
            "message": callback_query.message,
            "session": session_maker,
            "user_id": callback_query.from_user.id,
            "invoice_for_delete": invoice,
            "bot": bot,
            "apscheduler": apscheduler,
        }
    )
