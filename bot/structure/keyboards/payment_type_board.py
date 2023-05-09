from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import PaymentTypeStates

builder = InlineKeyboardBuilder()
builder.button(
    text="1 месяц", callback_data=PaymentTypeStates(sub_period=1)
)
builder.button(
    text="3 месяца", callback_data=PaymentTypeStates(sub_period=3)
)
builder.button(
    text="1 год", callback_data=PaymentTypeStates(sub_period=12)
)
builder.adjust(1)

PAYMENT_TYPE_BOARD = builder.as_markup()
