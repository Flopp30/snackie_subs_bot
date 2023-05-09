"""
start handler
"""
from aiogram import types
from aiogram.enums import ParseMode

from bot.structure.keyboards import START_BOARD
from bot.text_for_messages import TEXT_GREETING


async def start(message: types.Message) -> None:

    await message.answer(
        TEXT_GREETING,
        parse_mode=ParseMode.HTML,
        reply_markup=START_BOARD,
    )
