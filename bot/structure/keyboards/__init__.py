__all__ = [
    "START_BOARD",
    "get_payment_types_board",
    "AFTER_PAYMENT_REDIRECT_BOARD",
    "UNSUB_BOARD",
    "USER_GROUPS_BOARD",
    "SEND_MESSAGE_ACCEPT_BOARD",
    "get_payment_board",
    "CONFIRMATION_BOARD",
    "ADMIN_BOARD"
]

from bot.structure.keyboards.after_payment_redirect_board import AFTER_PAYMENT_REDIRECT_BOARD
from bot.structure.keyboards.get_payment_board import get_payment_board
from bot.structure.keyboards.payment_type_board import get_payment_types_board
from bot.structure.keyboards.send_message_accept_board import SEND_MESSAGE_ACCEPT_BOARD
from bot.structure.keyboards.start_board import START_BOARD
from bot.structure.keyboards.unsub_board import UNSUB_BOARD
from bot.structure.keyboards.users_groups_board import USER_GROUPS_BOARD
from bot.structure.keyboards.confirmation_board import CONFIRMATION_BOARD
from bot.structure.keyboards.admin_board import ADMIN_BOARD
