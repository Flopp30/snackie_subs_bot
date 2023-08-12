"""
Register handlers
"""
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command

from bot.handlers.help import help_command, help_func
from bot.handlers.start import start
from bot.handlers.administration import admin_start, send_messages_enter_a_text, send_message_confirmation, \
    send_messages_final, create_sale_enter_dates, create_sale_confirmation, remove_sale_confirmation, \
    remove_sale_enter_dates
from bot.handlers.subscription import subscription_start, send_subscribe_invoice
from bot.handlers.unsubscribtion import unsubscription_start, unsub_process
from bot.middleware import RegisterCheck
from bot.structure import StartStates, PaymentTypeStates, UnsubStates, AdminsCallBack, SendMessageState, \
    UserGroupsCallBack, SendMessageCallBack, CreateSaleState, ConfirmationCallBack, RemoveSaleState
from bot.text_for_messages import TEXT_UNKNOWN_MESSAGE

__all__ = [
    "register_user_commands",
]


def register_user_commands(router: Router) -> None:
    """
    Register user commands
    :param router:
    :return:
    """

    # middleware
    router.message.middleware(RegisterCheck())
    router.callback_query.middleware(RegisterCheck())
    # start
    router.message.register(start, CommandStart())

    # administrations
    router.callback_query.register(admin_start, AdminsCallBack.filter())
    router.callback_query.register(
        send_messages_enter_a_text,
        UserGroupsCallBack.filter(),
        SendMessageState.waiting_for_select_group
    )
    router.message.register(send_message_confirmation, SendMessageState.waiting_for_text)
    router.callback_query.register(
        send_messages_final,
        SendMessageCallBack.filter(),
        SendMessageState.waiting_for_confirm
    )

    router.message.register(create_sale_enter_dates, CreateSaleState.waiting_for_dates)
    router.callback_query.register(
        create_sale_confirmation,
        ConfirmationCallBack.filter(),
        CreateSaleState.waiting_for_confirm
    )

    router.message.register(remove_sale_enter_dates, RemoveSaleState.waiting_for_dates)
    router.callback_query.register(
        remove_sale_confirmation,
        ConfirmationCallBack.filter(),
        RemoveSaleState.waiting_for_confirm
    )

    # help
    router.message.register(help_command, Command(commands=["help"]))
    router.message.register(help_func, F.text.capitalize() == "Помощь")

    # unsubscribe
    router.message.register(unsubscription_start, F.text.capitalize() == "Отписаться")
    router.callback_query.register(unsub_process, UnsubStates.filter())

    # subscription
    router.callback_query.register(subscription_start, StartStates.filter())
    router.callback_query.register(send_subscribe_invoice, PaymentTypeStates.filter())

    # unknown command
    router.message.register(handle_unknown_message)


async def handle_unknown_message(message: types.Message):
    await message.answer(TEXT_UNKNOWN_MESSAGE)

