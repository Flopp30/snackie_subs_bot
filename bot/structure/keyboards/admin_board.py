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
builder.button(
    text="Забанить пользователя в других ботах",
    callback_data=AdminsCallBack(action=AdminsCDAction.BAN_USER_IN_OWNED_BOT)
)
builder.button(
    text="Разбанить пользователя в других ботах",
    callback_data=AdminsCallBack(action=AdminsCDAction.UNBAN_USER_IN_OWNED_BOT)
)
builder.button(
    text="Завершить текущие продажи", callback_data=AdminsCallBack(action=AdminsCDAction.STOP_SALE)
)
builder.button(
    text="Ввести даты новых продаж", callback_data=AdminsCallBack(action=AdminsCDAction.CREATE_NEW_SALE)
)

builder.adjust(1)

ADMIN_BOARD = builder.as_markup()
