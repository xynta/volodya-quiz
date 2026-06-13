"""Обработка ответов и подсказок во время игры."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, User

from game.engine import answer
from game.lifelines import audience_help, fifty_fifty, friend_call
from keyboards import game_over_keyboard, question_keyboard
from leaderboard import record_game
from session import load_game, save_game
from states import Quiz
from texts import render_game_over, render_question, render_reveal, render_standing_note

router = Router()


def display_name(user: User) -> str:
    """Имя игрока для лидерборда: имя+фамилия из Telegram, иначе @username,
    иначе id. У Telegram-пользователя first_name есть всегда, так что full_name
    практически всегда непустой."""
    return user.full_name or (f"@{user.username}" if user.username else f"id{user.id}")


def _render_audience(votes: dict[str, int]) -> str:
    lines = ["📊 Помощь зала:"]
    for letter in sorted(votes):
        filled = round(votes[letter] / 10)
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"{letter} {bar} {votes[letter]}%")
    return "\n".join(lines)


@router.callback_query(Quiz.playing, F.data.startswith("ans:"))
async def cb_answer(callback: CallbackQuery, state: FSMContext) -> None:
    game = await load_game(state)
    if game is None or game.finished:
        await callback.answer("Игра не активна. Нажми /play, чтобы начать.", show_alert=True)
        return

    letter = callback.data.split(":", 1)[1]
    if letter not in game.available_letters():
        await callback.answer()
        return

    await callback.answer()
    question = game.current  # фиксируем до перехода
    result = answer(game, letter)
    await save_game(state, game)

    # Подсветим итог по отвеченному вопросу, убрав кнопки.
    await callback.message.edit_text(render_reveal(question, result))

    if result.finished:
        await state.set_state(None)
        user = callback.from_user
        standing = record_game(user.id, display_name(user), result.final_amount, result.won)
        await callback.message.answer(
            render_game_over(result) + render_standing_note(standing),
            reply_markup=game_over_keyboard(),
        )
    else:
        await callback.message.answer(
            render_question(game), reply_markup=question_keyboard(game)
        )


@router.callback_query(Quiz.playing, F.data.startswith("ll:"))
async def cb_lifeline(callback: CallbackQuery, state: FSMContext) -> None:
    game = await load_game(state)
    if game is None or game.finished:
        await callback.answer("Игра не активна. Нажми /play, чтобы начать.", show_alert=True)
        return

    key = callback.data.split(":", 1)[1]
    if key not in game.lifelines or game.lifelines[key]:
        await callback.answer("Эта подсказка уже использована.", show_alert=True)
        return

    game.lifelines[key] = True
    question = game.current

    if key == "fifty":
        to_hide = fifty_fifty(question, game.hidden)
        game.hidden = list(set(game.hidden) | set(to_hide))
        await save_game(state, game)
        await callback.answer("Убрали два неверных варианта!")
        await callback.message.edit_text(
            render_question(game), reply_markup=question_keyboard(game)
        )
        return

    if key == "audience":
        votes = audience_help(question, game.hidden)
        await save_game(state, game)
        await callback.message.edit_reply_markup(reply_markup=question_keyboard(game))
        await callback.answer(_render_audience(votes), show_alert=True)
        return

    if key == "friend":
        text = friend_call(question, game.hidden)
        await save_game(state, game)
        await callback.message.edit_reply_markup(reply_markup=question_keyboard(game))
        await callback.answer(f"📞 Звонок другу:\n\n{text}", show_alert=True)
        return
