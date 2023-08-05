"""
statistic handler
"""
import asyncio
import logging

from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.orm import sessionmaker

from bot.handlers import start
from bot.structure import AdminsCDAction, AdminsCallBack, SendMessageState, UserGroupsCallBack, UserGroupsCD, \
    SendMessageCallBack, SendMessageActionsCD
from bot.structure.keyboards import USER_GROUPS_BOARD, SEND_MESSAGE_ACCEPT_BOARD
from bot.utils import get_users_by_group
from bot.utils.statistic import get_user_stat, get_payment_stat


async def admin_start(
        callback_query: types.CallbackQuery,
        get_async_session: sessionmaker,
        callback_data: AdminsCallBack,
        state: FSMContext,
) -> None:
    async with get_async_session() as session:
        if callback_data.action == AdminsCDAction.PAYMENT_STAT:
            report_message, csv_file = await get_payment_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="payments.csv"
                )
            )
        elif callback_data.action == AdminsCDAction.USER_STAT:
            report_message, csv_file = await get_user_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="users_report.csv"
                )
            )
        elif callback_data.action == AdminsCDAction.SEND_MESSAGE:
            await state.set_state(SendMessageState.waiting_for_select_group)
            await callback_query.message.answer('Выбери группу', reply_markup=USER_GROUPS_BOARD)


async def send_message_start(
        message: types.Message,
        state: FSMContext,
):
    await state.set_state(SendMessageState.waiting_for_select_group)
    await message.answer('Выбери группу', reply_markup=USER_GROUPS_BOARD)


async def send_messages_enter_a_text(
        callback_query: types.CallbackQuery,
        callback_data: UserGroupsCallBack,
        state: FSMContext,
) -> None:
    await state.update_data(group=callback_data.group)
    await state.set_state(SendMessageState.waiting_for_text)
    group = ''
    match callback_data.group:
        case UserGroupsCD.ALL_USERS:
            group = 'Все пользователи'
        case UserGroupsCD.SUB_USERS:
            group = 'Подписанные пользователи'
        case UserGroupsCD.UNSUB_USERS:
            group = 'Неподписанные пользователи'
        case UserGroupsCD.SEVEN_DAYS_USERS:
            group = 'Недельки'
        case UserGroupsCD.ONE_MONTH_USERS:
            group = 'Месячники'
        case UserGroupsCD.THREE_MONTHS_USERS:
            group = 'Три месяца'
        case UserGroupsCD.ONE_YEAR_USERS:
            group = 'Годовые шейхи'
    await callback_query.message.answer(
        f'Выбранная группа: {group} \n'
        'Пришли текст сообщения.\n'
        '"Отмена" - чтобы вернуться к выбору группы\n'
        '"Домой" - на старт'
    )


async def send_message_confirmation(
        message: types.Message,
        get_async_session: sessionmaker,
        state: FSMContext,
):
    if message.text.lower() == "отмена":
        await state.get_data()
        return await send_message_start(message, state)
    elif message.text.lower() == "домой":
        await state.get_data()
        return await start(message, get_async_session)

    await state.set_state(SendMessageState.waiting_for_confirm)
    await state.update_data(message=message.text)

    await message.answer("Сообщение будет выглядеть так:")
    await asyncio.sleep(0.5)
    await message.answer(message.text)
    await asyncio.sleep(0.5)
    await message.answer('Отправляем?', reply_markup=SEND_MESSAGE_ACCEPT_BOARD)


async def send_messages_final(
        callback_query: types.CallbackQuery,
        callback_data: SendMessageCallBack,
        get_async_session: sessionmaker,
        state: FSMContext,
        bot,
) -> None:
    data = await state.get_data()
    group = data.get('group')
    message = data.get('message')
    match callback_data.action:

        case SendMessageActionsCD.EDIT_TEXT:
            return await send_messages_enter_a_text(
                callback_query,
                UserGroupsCallBack(group=UserGroupsCD(group)),
                state,
            )

        case SendMessageActionsCD.CHANGE_GROUP:
            return await admin_start(
                callback_query,
                get_async_session,
                AdminsCallBack(action=AdminsCDAction.SEND_MESSAGE),
                state,
            )

        case SendMessageActionsCD.ACCEPT:
            async with get_async_session() as session:
                users = await get_users_by_group(group, session)
                if users:
                    counter_success = 0
                    for user in users:
                        try:
                            await bot.send_message(
                                chat_id=user.id,
                                text=message,
                            )
                        except Exception as e:
                            logging.error(e)
                        else:
                            counter_success += 1
                    await callback_query.message.answer(f"Отправлено сообщений: {counter_success}")
                else:
                    await callback_query.message.answer(f"Пользователей этой группу не найдено :(")
                    return await admin_start(
                        callback_query,
                        get_async_session,
                        AdminsCallBack(action=AdminsCDAction.SEND_MESSAGE),
                        state,
                    )

