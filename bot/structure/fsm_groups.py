"""
FSM groups
"""


from aiogram.fsm.state import StatesGroup, State


class SendMessageState(StatesGroup):
    """
        States for broadcasting messages
    """
    waiting_for_select_group = State()
    waiting_for_text = State()
    waiting_for_confirm = State()


class CreateSaleState(StatesGroup):
    """
        States for new sale creating
    """
    waiting_for_dates = State()
    waiting_for_confirm = State()

class RemoveSaleState(StatesGroup):
    """
        States for new sale creating
    """
    waiting_for_dates = State()
    waiting_for_confirm = State()
