"""
admins handlers
"""
import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.orm import sessionmaker

from bot.handlers import start
from bot.structure import AdminsCDAction, AdminsCallBack, SendMessageState, UserGroupsCallBack, UserGroupsCD, \
    SendMessageCallBack, SendMessageActionsCD, GROUP_NAMES
from bot.structure.keyboards import USER_GROUPS_BOARD, SEND_MESSAGE_ACCEPT_BOARD
from bot.utils import get_users_by_group, bot_send_message, CustomCounter
from bot.utils.statistic import get_user_stat, get_payment_stat


async def admin_start(
        callback_query: types.CallbackQuery,
        get_async_session: sessionmaker,
        callback_data: AdminsCallBack,
        state: FSMContext,
) -> None:
    """
        admins start handler
    """
    async with get_async_session() as session:
        if callback_data.action == AdminsCDAction.PAYMENT_STAT:  # Statistic by payments
            report_message, csv_file = await get_payment_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="payments.csv"
                )
            )
        elif callback_data.action == AdminsCDAction.USER_STAT:  # Statistic by users
            report_message, csv_file = await get_user_stat(session)
            await callback_query.message.answer(report_message)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="users_report.csv"
                )
            )
        elif callback_data.action == AdminsCDAction.SEND_MESSAGE:  # Sending message for user's groups
            await state.set_state(SendMessageState.waiting_for_select_group)  # set state - waiting for group
            await callback_query.message.answer('Выбери группу', reply_markup=USER_GROUPS_BOARD)


async def send_message_start(
        message: types.Message,
        state: FSMContext,
):
    """
    Needs for return by message (check async def send_message_confirmation on line 86)
    """
    await state.set_state(SendMessageState.waiting_for_select_group)  # set state - waiting for group
    await message.answer('Выбери группу', reply_markup=USER_GROUPS_BOARD)


async def send_messages_enter_a_text(
        callback_query: types.CallbackQuery,
        callback_data: UserGroupsCallBack,
        state: FSMContext,
) -> None:
    """
    Enter a text handler
    """
    await state.update_data(group=callback_data.group)  # add to context selected group
    await state.set_state(SendMessageState.waiting_for_text)  # set state - waiting for message text

    group = GROUP_NAMES.get(callback_data.group, 'Неизвестная группа')
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
    """
     show the admin a message to send to the group and get the final confirmation
    """
    if message.text.lower() == "отмена":  # return to changing group
        await state.get_data()
        return await send_message_start(message, state)
    elif message.text.lower() == "домой":  # return to start handler
        await state.get_data()
        return await start(message, get_async_session)

    await state.set_state(SendMessageState.waiting_for_confirm)  # set state - waiting for confirmation
    await state.update_data(message=message.text)  # add to context message.text

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
    """
    Send message final handler
    """

    data = await state.get_data()
    group, message = data.get('group'), data.get('message')  # get by context selected group and message.text

    match callback_data.action:

        case SendMessageActionsCD.EDIT_TEXT:  # return to edit text
            return await send_messages_enter_a_text(
                callback_query,
                UserGroupsCallBack(group=UserGroupsCD(group)),
                state,
            )

        case SendMessageActionsCD.CHANGE_GROUP:  # return to change group
            return await admin_start(
                callback_query,
                get_async_session,
                AdminsCallBack(action=AdminsCDAction.SEND_MESSAGE),
                state,
            )

        case SendMessageActionsCD.ACCEPT:  # sending message for users
            async with get_async_session() as session:
                users = await get_users_by_group(
                    group=group,
                    session=session
                )
                if users:
                    count_success = CustomCounter()
                    count_error = CustomCounter()
                    count_blocked = CustomCounter()
                    tasks = [
                        bot_send_message(
                            bot,
                            message,
                            user.id,
                            count_blocked,
                            count_error,
                            count_success,
                        ) for user in users
                    ]
                    await asyncio.gather(*tasks)
                    await callback_query.message.answer(f"Отправлено сообщений: {count_success}\n"
                                                        f"Бот в бане: {count_blocked}\n"
                                                        f"Ошибок: {count_error}")
                else:
                    await callback_query.message.answer("Пользователей этой группы не найдено :(")
                    return await admin_start(
                        callback_query,
                        get_async_session,
                        AdminsCallBack(action=AdminsCDAction.SEND_MESSAGE),
                        state,
                    )
