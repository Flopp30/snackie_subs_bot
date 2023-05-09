import asyncio

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import sessionmaker

from bot.db import Payment, set_subscribe_after_payment
from bot.structure import PaymentTypeStates
from bot.structure.keyboards import PAYMENT_TYPE_BOARD, AFTER_PAYMENT_REDIRECT_BOARD
from bot.text_for_messages import TEXT_SUCCESSFUL_PAYMENT
from bot.utils import get_tariffs_text, get_invoice_params


async def payment_start(
        callback_query: types.CallbackQuery,
        session_maker: sessionmaker,
        state: FSMContext
) -> None:
    text = await get_tariffs_text(session_maker=session_maker, state=state)
    await callback_query.message.edit_text(
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=PAYMENT_TYPE_BOARD,
    )


async def send_subscribe_invoice(
        callback_query: types.CallbackQuery,
        callback_data: PaymentTypeStates,
        state: FSMContext
) -> None:
    await callback_query.message.delete()

    state_data: dict = await state.get_data()
    payments: list = state_data.get("payments", "")

    current_payment: Payment | None = None

    for payment in payments:
        if payment.sub_period == callback_data.sub_period:
            current_payment = payment
            break

    if current_payment:
        invoice_params = await get_invoice_params(payment=current_payment)
        await callback_query.message.answer_invoice(**invoice_params)
    else:
        pass
        # TODO добавить обработку и логи


async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True, error_message="Something went wrong. Please, contact tech")


async def got_payment(message: types.Message, session_maker: sessionmaker):
    sub_period = int(message.successful_payment.invoice_payload)
    sub_period_text = "1 месяц"
    match sub_period:
        case 1:
            pass
        case 3:
            sub_period_text = "3 месяца"
        case 12:
            sub_period_text = "1 год"
    await message.answer(
        f"Оплата на сумму {message.successful_payment.total_amount // 100} "
        f"{message.successful_payment.currency} прошла успешно.\n"
        f"Оформлена подписка на {sub_period_text}"
    )
    await set_subscribe_after_payment(
        user_id=message.from_user.id,
        sub_period=sub_period,
        session=session_maker
    )
    await asyncio.sleep(0.5)
    await message.answer(text=TEXT_SUCCESSFUL_PAYMENT, reply_markup=AFTER_PAYMENT_REDIRECT_BOARD)
