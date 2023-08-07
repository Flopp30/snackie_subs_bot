from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.structure import UserGroupsCallBack, UserGroupsCD

builder = InlineKeyboardBuilder()

builder.button(
    text="Все пользователи", callback_data=UserGroupsCallBack(group=UserGroupsCD.ALL_USERS)
)
builder.button(
    text="Все неподписанные пользователи", callback_data=UserGroupsCallBack(group=UserGroupsCD.UNSUB_USERS)
)
builder.button(
    text="Все подписанные пользователи", callback_data=UserGroupsCallBack(group=UserGroupsCD.SUB_USERS)
)
builder.button(
    text="Активные недельки", callback_data=UserGroupsCallBack(group=UserGroupsCD.SEVEN_DAYS_USERS)
)
builder.button(
    text="Активный месяц", callback_data=UserGroupsCallBack(group=UserGroupsCD.ONE_MONTH_USERS)
)
builder.button(
    text="Активные 3 месяца", callback_data=UserGroupsCallBack(group=UserGroupsCD.THREE_MONTHS_USERS)
)
builder.button(
    text="Годовики", callback_data=UserGroupsCallBack(group=UserGroupsCD.ONE_YEAR_USERS)
)
builder.adjust(1)

USER_GROUPS_BOARD = builder.as_markup()
