"""
Callback datas
"""
import enum

from aiogram.filters.callback_data import CallbackData


class StartStates(CallbackData, prefix="start"):
    action: str


class PaymentTypeStates(CallbackData, prefix="payment"):
    sub_period: int  # 1, 3, 12


class UnsubStates(CallbackData, prefix="unsub"):
    answer: str  # Yes / No


class StatisticCDAction(enum.IntEnum):
    """
        Statistic actions
    """
    ACTIVE_USER = 0
    PAYMENT_STAT = 1
    ALL_TIME_STAT = 2


class StatisticCallBack(CallbackData, prefix="statistic"):
    """
    Statistic callback
    """
    action: StatisticCDAction
