"""FSM-состояния игрока."""
from aiogram.fsm.state import State, StatesGroup


class Quiz(StatesGroup):
    playing = State()
