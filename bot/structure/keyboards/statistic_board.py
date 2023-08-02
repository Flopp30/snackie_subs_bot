from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import StatisticCallBack, StatisticCDAction

builder = InlineKeyboardBuilder()
builder.button(
    text="Отчет по пользователям", callback_data=StatisticCallBack(action=StatisticCDAction.USER_STAT)
)
builder.button(
    text="Отчет по платежам", callback_data=StatisticCallBack(action=StatisticCDAction.PAYMENT_STAT)
)
builder.adjust(1)

STATISTIC_BOARD = builder.as_markup()
