from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import UnsubStates

builder = InlineKeyboardBuilder()
builder.button(
    text="Да, точно хочу отписаться", callback_data=UnsubStates(answer="Yes")
)
builder.button(
    text="Нет, остаюсь, я машина фитнеса", callback_data=UnsubStates(answer="No")
)
builder.adjust(1)

UNSUB_BOARD = builder.as_markup()
