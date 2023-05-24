from aiogram.types import WebAppInfo, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_payment_board(payment_amount: int, payment_currency: str, url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Оплатить {payment_amount} {payment_currency}",
        web_app=WebAppInfo(url=url),
    ).adjust(1)
    return builder.as_markup()
