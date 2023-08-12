from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import ConfirmationCallBack


builder = InlineKeyboardBuilder()

builder.button(
    text="Подтвердить", callback_data=ConfirmationCallBack(action='confirm')
)
builder.button(
    text="Отменить", callback_data=ConfirmationCallBack(action='cancel')
)
builder.adjust(1)

CONFIRMATION_BOARD = builder.as_markup()
