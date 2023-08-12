"""
Register handlers
"""
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command

from bot.handlers.help import help_command, help_func
from bot.handlers.start import start
from bot.handlers.administration import admin_start, send_messages_enter_a_text, send_message_confirmation, \
    send_messages_final, create_sale_enter_dates, create_sale_confirmation, remove_sale_confirmation, \
    action_with_user_in_owned_bot_choose_user, action_with_user_in_owned_bot_confirm, \
    action_with_user_in_owned_bot_final, remove_sale_enter_dates
from bot.handlers.subscription import subscription_start, send_subscribe_invoice
from bot.handlers.unsubscribtion import unsubscription_start, unsub_process
from bot.middleware import RegisterCheck
from bot.structure import StartStates, PaymentTypeStates, UnsubStates, AdminsCallBack, SendMessageState, \
    UserGroupsCallBack, SendMessageCallBack, CreateSaleState, ConfirmationCallBack, RemoveSaleState, \
    ActionsWithUserInOwnedBotsState, BotSelectionCallBack
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

    # MIDDLEWARE
    router.message.middleware(RegisterCheck())
    router.callback_query.middleware(RegisterCheck())

    # START
    router.message.register(start, CommandStart())

    # ADMINISTRATION
    router.callback_query.register(admin_start, AdminsCallBack.filter())
    # message broadcasting
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
    # sales
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
    # ban / unban user in owned bots from admin
    router.callback_query.register(
        action_with_user_in_owned_bot_choose_user,
        BotSelectionCallBack.filter(),
        ActionsWithUserInOwnedBotsState.waiting_for_choose_owned_bot
    )
    router.message.register(action_with_user_in_owned_bot_confirm, ActionsWithUserInOwnedBotsState.waiting_for_id)
    router.callback_query.register(
        action_with_user_in_owned_bot_final,
        ConfirmationCallBack.filter(),
        ActionsWithUserInOwnedBotsState.waiting_for_confirm,
    )

    # HELP
    router.message.register(help_command, Command(commands=["help"]))
    router.message.register(help_func, F.text.capitalize() == "Помощь")

    # UNSUBSCRIBE
    router.message.register(unsubscription_start, F.text.capitalize() == "Отписаться")
    router.callback_query.register(unsub_process, UnsubStates.filter())

    # SUBSCRIPTION
    router.callback_query.register(subscription_start, StartStates.filter())
    router.callback_query.register(send_subscribe_invoice, PaymentTypeStates.filter())

    # UNKNOWN COMMAND
    router.message.register(handle_unknown_message)


async def handle_unknown_message(message: types.Message):
    await message.answer(TEXT_UNKNOWN_MESSAGE)
