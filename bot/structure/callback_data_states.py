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


class AdminsCDAction(enum.IntEnum):
    """
        Admins actions
    """
    USER_STAT = 0
    PAYMENT_STAT = 1
    SEND_MESSAGE = 2
    STOP_SALE = 3
    CREATE_NEW_SALE = 4


class AdminsCallBack(CallbackData, prefix="statistic"):
    """
        Admins callback
    """
    action: AdminsCDAction


class UserGroupsCD(enum.IntEnum):
    """
        User types
    """
    ALL_USERS = 0
    UNSUB_USERS = 1
    SUB_USERS = 2
    SEVEN_DAYS_USERS = 3
    ONE_MONTH_USERS = 4
    THREE_MONTHS_USERS = 5
    ONE_YEAR_USERS = 6


GROUP_NAMES = {
    UserGroupsCD.ALL_USERS: 'Все пользователи',
    UserGroupsCD.SUB_USERS: 'Подписанные пользователи',
    UserGroupsCD.UNSUB_USERS: 'Неподписанные пользователи',
    UserGroupsCD.SEVEN_DAYS_USERS: 'Недельки',
    UserGroupsCD.ONE_MONTH_USERS: 'Месячники',
    UserGroupsCD.THREE_MONTHS_USERS: 'Три месяца',
    UserGroupsCD.ONE_YEAR_USERS: 'Годовые шейхи',
}


class UserGroupsCallBack(CallbackData, prefix="messages"):
    """
    Statistic callback
    """
    group: UserGroupsCD


class SendMessageActionsCD(enum.IntEnum):
    """
        Send message actions
    """
    ACCEPT = 0
    EDIT_TEXT = 1
    CHANGE_GROUP = 2


class SendMessageCallBack(CallbackData, prefix="send_messages"):
    """
    Send message callback
    """
    action: SendMessageActionsCD


class ConfirmationCallBack(CallbackData, prefix="confirmation"):
    """
    Reusable confirmation callback
    """
    action: str  # confirm / cancel
