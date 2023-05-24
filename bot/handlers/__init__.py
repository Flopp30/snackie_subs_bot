"""
Register handlers
"""
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command

from bot.handlers.help import help_command, help_func
from bot.handlers.start import start
from bot.handlers.subscription import subscription_start, send_subscribe_invoice
from bot.handlers.unsubscribtion import unsubscription_start, unsub_process
from bot.middleware import RegisterCheck
from bot.structure import StartStates, PaymentTypeStates, UnsubStates
from bot.text_for_messages import BOT_COMMANDS_INFO, TEXT_UNKNOWN_MESSAGE

__all__ = [
    "BOT_COMMANDS_INFO",
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
