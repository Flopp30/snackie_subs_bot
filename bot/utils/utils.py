from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from bot.db import Payment
from bot.settings import YOOKASSA_KEY
from bot.text_for_messages import TEXT_TARIFFS, TEXT_TARIFFS_DETAIL


async def get_tariffs_text(session_maker: sessionmaker, state: FSMContext) -> str:
    async with session_maker() as session:
        async with session.begin():
            payments = (await session.execute(select(Payment))).scalars()
    text = TEXT_TARIFFS
    state_payments = []
    for payment in payments:
        text += TEXT_TARIFFS_DETAIL.format(
            humanize_name=payment.humanize_name,
            payment_period_name=payment.payment_name,
            payment_amount=payment.payment_amount / 100,
            payment_currency=payment.payment_currency)
        state_payments.append(payment)
    await state.update_data(payments=state_payments)
    return text


async def get_invoice_params(payment: Payment) -> dict:
    # TODO не забыть поправить сумму после окончания тестирования
    price = [
        LabeledPrice(label=payment.payment_currency, amount=payment.payment_amount / 10)
    ]

    res = {
        "title": payment.payment_name,
        "description": payment.humanize_name,
        "provider_token": YOOKASSA_KEY,
        "currency": payment.payment_currency,
        "prices": price,
        "payload": payment.sub_period,
    }

    return res
