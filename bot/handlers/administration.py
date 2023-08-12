"""
admins handlers
"""
import asyncio
from datetime import datetime

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from sqlalchemy.orm import sessionmaker

from bot.handlers import start
from bot.structure import AdminsCDAction, AdminsCallBack, SendMessageState, UserGroupsCallBack, UserGroupsCD, \
    SendMessageCallBack, ConfirmationCallBack, SendMessageActionsCD, CreateSaleState, RemoveSaleState, GROUP_NAMES
from bot.structure.keyboards import USER_GROUPS_BOARD, SEND_MESSAGE_ACCEPT_BOARD, CONFIRMATION_BOARD, ADMIN_BOARD
from bot.text_for_messages import TEXT_ENTER_NEW_SALES_DATES, TEXT_ENTER_DEACTIVATE_SALE
from bot.utils import get_users_by_group, bot_send_message, CustomCounter, check_dates, get_active_sales_text, \
    check_dates_for_remove
from bot.utils.statistic import get_user_stat, get_payment_stat, get_sales_dates_info
from bot.db.crud import sales_crud


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

        elif callback_data.action == AdminsCDAction.STOP_SALE:
            active_sales_text = await get_active_sales_text(session)
            if active_sales_text == 'Нет запланированных периодов продаж':
                await callback_query.message.answer(active_sales_text)
            else:
                await state.set_state(RemoveSaleState.waiting_for_dates)
                await callback_query.message.answer(
                    f'{active_sales_text}\n'
                    f'{TEXT_ENTER_DEACTIVATE_SALE}'
                )

        elif callback_data.action == AdminsCDAction.CREATE_NEW_SALE:
            await state.set_state(CreateSaleState.waiting_for_dates)
            await callback_query.message.answer(TEXT_ENTER_NEW_SALES_DATES)

        elif callback_data.action == AdminsCDAction.GET_SALE_DATES_LIST:
            text = await get_active_sales_text(session)
            csv_file = await get_sales_dates_info(session)
            await callback_query.message.answer_document(
                BufferedInputFile(
                    csv_file,
                    filename="sales_dates.csv"
                )
            )
            await callback_query.message.answer(text)


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


async def create_sale_enter_dates(
        message: types.Message,
        get_async_session: sessionmaker,
        state: FSMContext,
) -> None:
    """
    Enter new sales dates handler
    """
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer('Операция отменена')
        await message.answer(
        text="Административная часть",
        reply_markup=ADMIN_BOARD,
    )
    else:
        async with get_async_session() as session:
            start_date, end_date, error = await check_dates(message.text, session)
        if error:
            await message.answer(error)
        else:
            await state.update_data(start_date=str(start_date), end_date=str(end_date))
            await state.set_state(CreateSaleState.waiting_for_confirm)
            await message.answer(
                f'Подтверди период продаж: {start_date:%d.%m.%Y} - {end_date:%d.%m.%Y}',
                reply_markup=CONFIRMATION_BOARD
            )

async def create_sale_confirmation(
    callback_query: types.CallbackQuery,
    callback_data: ConfirmationCallBack,
    get_async_session: sessionmaker,
    state: FSMContext,
    ) -> None:
    """
    Confirm new sales dates handler
    """
    if callback_data.action == 'confirm':
        async with get_async_session() as session:
            dates = await state.get_data()
            sales_start = datetime.fromisoformat(dates.get('start_date'))
            sales_finish = datetime.fromisoformat(dates.get('end_date'))
            await sales_crud.create(
                obj_in_data={
                    'sales_start': sales_start,
                    'sales_finish': sales_finish,
                    'is_active': True
                },
                session=session
            )
            await callback_query.message.answer(
                f'Период продаж {sales_start:%d.%m.%Y} - {sales_finish:%d.%m.%Y} сохранен'
            )
    else:
        await callback_query.message.answer('Операция отменена')
    await state.clear()
    await callback_query.message.answer(
        text="Административная часть",
        reply_markup=ADMIN_BOARD,
    )


async def remove_sale_enter_dates(
        message: types.Message,
        get_async_session: sessionmaker,
        state: FSMContext,
) -> None:
    """
    Enter new sales dates handler
    """
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer('Операция отменена')
        await message.answer(
        text="Административная часть",
        reply_markup=ADMIN_BOARD,
    )
    else:
        async with get_async_session() as session:
            sale_id, start_date, end_date, error = await check_dates_for_remove(
                message.text, session
            )
        if error:
            await message.answer(error)
        else:
            await state.update_data(
                start_date=str(start_date),
                end_date=str(end_date),
                sale_id=sale_id
            )
            await state.set_state(RemoveSaleState.waiting_for_confirm)
            await message.answer(
                f'Подтверди отмену акции в период: {start_date:%d.%m.%Y} - {end_date:%d.%m.%Y}',
                reply_markup=CONFIRMATION_BOARD
            )


async def remove_sale_confirmation(
    callback_query: types.CallbackQuery,
    callback_data: ConfirmationCallBack,
    get_async_session: sessionmaker,
    state: FSMContext,
    ) -> None:
    """
    Confirm current sale remove handler
    """
    if callback_data.action == 'confirm':
        async with get_async_session() as session:
            data = await state.get_data()
            current_sale_id = data.get('sale_id')
            current_sale = await sales_crud.get_by_id(current_sale_id, session)
            await sales_crud.update(current_sale, {'is_active': False}, session)
            await callback_query.message.answer(
                f'Продажи в период '
                f'{current_sale.sales_start:%d.%m.%Y} - {current_sale.sales_finish:%d.%m.%Y} '
                f'остановлены.'
            )
    else:
        await callback_query.message.answer('Операция отменена')

    await state.clear()
    await callback_query.message.answer(
        text="Административная часть",
        reply_markup=ADMIN_BOARD,
    )


