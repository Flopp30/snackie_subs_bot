from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import AdminsCallBack, AdminsCDAction

builder = InlineKeyboardBuilder()
builder.button(
    text="Отчет по пользователям", callback_data=AdminsCallBack(action=AdminsCDAction.USER_STAT)
)
builder.button(
    text="Отчет по платежам", callback_data=AdminsCallBack(action=AdminsCDAction.PAYMENT_STAT)
)
builder.button(
    text="Отправить сообщение пользователям", callback_data=AdminsCallBack(action=AdminsCDAction.SEND_MESSAGE)
)
builder.adjust(1)

ADMIN_BOARD = builder.as_markup()
