"""
statistic handler
"""

from aiogram import types
from aiogram.types import BufferedInputFile
from sqlalchemy.orm import sessionmaker

from bot.structure import StatisticCDAction, StatisticCallBack
from bot.utils.statistic import get_user_stat, get_payment_stat


async def statistic(
        callback_query: types.CallbackQuery,
        get_async_session: sessionmaker,
        callback_data: StatisticCallBack,
) -> None:
    async with get_async_session() as session:
        if callback_data.action == StatisticCDAction.PAYMENT_STAT:
            report_message, csv_file = await get_payment_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="payments.csv"
                )
            )
        elif callback_data.action == StatisticCDAction.USER_STAT:
            report_message, csv_file = await get_user_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="users_report.csv"
                )
            )
