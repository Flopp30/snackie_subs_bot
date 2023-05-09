from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import StartStates

builder = InlineKeyboardBuilder()
builder.button(
    text="Хочу в клуб!", callback_data=StartStates(action="accepted")
)
builder.adjust(1)

START_BOARD = builder.as_markup()
