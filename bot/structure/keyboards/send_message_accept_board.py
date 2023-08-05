from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import SendMessageCallBack, SendMessageActionsCD

builder = InlineKeyboardBuilder()

builder.button(
    text="Да!", callback_data=SendMessageCallBack(action=SendMessageActionsCD.ACCEPT)
)
builder.button(
    text="Вернуться к редактированию текста", callback_data=SendMessageCallBack(action=SendMessageActionsCD.EDIT_TEXT)
)
builder.button(
    text="Вернуться к выбору группы", callback_data=SendMessageCallBack(action=SendMessageActionsCD.CHANGE_GROUP)
)
builder.adjust(1)

SEND_MESSAGE_ACCEPT_BOARD = builder.as_markup()
