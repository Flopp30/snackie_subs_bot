"""
Callback datas
"""
from aiogram.filters.callback_data import CallbackData


class StartStates(CallbackData, prefix="start"):
    action: str


class PaymentTypeStates(CallbackData, prefix="payment"):
    sub_period: int  # 1, 3, 12


class UnsubStates(CallbackData, prefix="unsub"):
    answer: str  # Yes / No
