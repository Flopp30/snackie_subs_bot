from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.settings import OWNED_BOTS
from bot.structure import BotSelectionCallBack, SelectionBotsCD

builder = InlineKeyboardBuilder()

for bot in OWNED_BOTS:
    builder.button(
        text=bot.rus_name,
        callback_data=BotSelectionCallBack(
            bot=SelectionBotsCD(bot.name)
        )
    )
builder.button(
    text='Все',
    callback_data=BotSelectionCallBack(
        bot=SelectionBotsCD.ALL
    )
)

builder.adjust(1)

BOT_SELECTION_BOARD = builder.as_markup()
