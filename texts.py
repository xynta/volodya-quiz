"""Сборка текстов сообщений в антураже «Званого ужина»."""
from config import QUESTIONS_PER_GAME
from game.engine import GameState, AnswerResult
from game.ladder import prize_for_level, guaranteed_level

WELCOME = (
    "🍽️ <b>Викторина «Кто хочет стать миллионером»</b>\n"
    "<i>По мотивам эпизода «Званый ужин с Ольгой Стукаловой» (РЕН ТВ)</i>\n\n"
    "Тебя ждёт лесенка из 15 вопросов — от простых до каверзных. "
    "Один неверный ответ завершает игру, но на 5-м и 10-м уровнях есть "
    "🔒 несгораемые призы.\n\n"
    "В запасе три подсказки: 50:50, помощь зала и звонок другу.\n\n"
    "Готов(а) сесть за стол? Жми «Играть»!"
)

HELP = (
    "🍽️ <b>Как играть</b>\n\n"
    "• /play — начать новую игру\n"
    "• 15 вопросов по нарастающей сложности\n"
    "• Отвечай, нажимая кнопку с буквой варианта\n"
    "• Неверный ответ завершает игру\n"
    "• 🔒 уровни 5 и 10 — несгораемые\n"
    "• Подсказки: 50:50, 📊 помощь зала, 📞 звонок другу (по одной на игру)\n"
)


def render_question(state: GameState) -> str:
    level = state.level
    guaranteed = guaranteed_level(level - 1)
    guaranteed_txt = prize_for_level(guaranteed) if guaranteed else "—"

    q = state.current
    options = "\n".join(
        f"<b>{letter})</b> {q['options'][letter]}"
        for letter in state.available_letters()
    )
    return (
        f"💚 <b>Вопрос {level} из {QUESTIONS_PER_GAME}</b>\n"
        f"🏆 Играем за: <i>{prize_for_level(level)}</i>\n"
        f"🔒 Несгораемое: <i>{guaranteed_txt}</i>\n\n"
        f"{q['question']}\n\n"
        f"{options}"
    )


def render_reveal(question: dict, result: AnswerResult) -> str:
    """Короткий итог по отвеченному вопросу (для редактирования сообщения)."""
    correct_letter = result.correct_letter
    correct_text = question["options"][correct_letter]
    if result.correct:
        return (
            f"✅ <b>Верно!</b> {result.chosen}) {question['options'][result.chosen]}\n"
            f"Забрано: <i>{result.final_prize}</i>"
        )
    return (
        f"❌ <b>Увы, неверно.</b> Ты выбрал(а) {result.chosen}.\n"
        f"Правильный ответ: <b>{correct_letter})</b> {correct_text}"
    )


def render_game_over(result: AnswerResult) -> str:
    if result.won:
        return (
            "🎉 <b>ПОБЕДА!</b> Ты ответил(а) на все 15 вопросов!\n"
            f"🏆 Главный приз: <b>{result.final_prize}</b>\n\n"
            "Ольга Стукалова аплодирует стоя! 👏 Жми «Играть ещё», чтобы повторить."
        )
    if result.level_reached <= 0:
        body = "Ты не взял(а) ни одного уровня — но это только начало!"
    else:
        body = (
            f"Ты дошёл(ла) до уровня <b>{result.level_reached}</b> из 15.\n"
            f"Забираешь: <b>{result.final_prize}</b>"
        )
    return f"🏁 <b>Игра окончена.</b>\n{body}\n\nПопробуем ещё раз?"
