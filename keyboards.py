"""Inline-клавиатуры."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from game.engine import GameState

LIFELINE_LABELS = {
    "fifty": "50:50",
    "audience": "📊 Помощь зала",
    "friend": "📞 Звонок другу",
}


def question_keyboard(state: GameState) -> InlineKeyboardMarkup:
    """Кнопки вариантов (только доступные) + ряд неиспользованных подсказок."""
    builder = InlineKeyboardBuilder()

    letters = state.available_letters()
    for letter in letters:
        builder.button(text=letter, callback_data=f"ans:{letter}")
    builder.adjust(len(letters))  # все буквы в один ряд

    lifeline_buttons = [
        InlineKeyboardButton(text=label, callback_data=f"ll:{key}")
        for key, label in LIFELINE_LABELS.items()
        if not state.lifelines[key]
    ]
    if lifeline_buttons:
        builder.row(*lifeline_buttons)

    return builder.as_markup()


def play_keyboard(text: str = "▶️ Играть") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data="play")
    return builder.as_markup()
