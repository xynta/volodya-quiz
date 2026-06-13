"""Сборка текстов сообщений в антураже «Званого ужина»."""
import html

from config import QUESTIONS_PER_GAME
from game.engine import GameState, AnswerResult
from game.ladder import (
    format_rubles,
    guaranteed_level,
    prize_bonus_text,
    prize_for_level,
)

WELCOME = (
    "🍽️ <b>Викторина «Кто хочет стать миллионером»</b>\n"
    "<i>По мотивам «Званого ужина» (РЕН ТВ)</i>\n\n"
    "Каждая игра — случайный вечер недели с одним из героев передачи. "
    "Тебя ждёт денежная лесенка из 15 вопросов: от 100 рублей до миллиона. "
    "Один неверный ответ завершает игру, но 1 000 ₽ (ур. 5) и 32 000 ₽ "
    "(ур. 10) — 🔒 несгораемые.\n\n"
    "В запасе три подсказки: 50:50, помощь зала и звонок другу.\n\n"
    "Все унесённые несгораемые суммы складываются в общий зачёт — /top "
    "покажет, кто заработал больше всех.\n\n"
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
    "• /top — 🏆 лидерборд: сумма унесённых несгораемых по всем игрокам\n"
)

# Инструкция по запуску консольной версии одной командой. Игра — это
# PowerShell-скрипт quiz.ps1 в репозитории: команда скачивает его и
# выполняет прямо в консоли, без установки Python и без скачивания файлов.
CMD_INSTRUCTIONS = (
    "💻 <b>Запуск в консоли — без установок</b>\n\n"
    "Игра запускается прямо в командной строке Windows 10/11. "
    "Ничего ставить не нужно: ни Python, ни файлов на диск.\n\n"
    "<b>PowerShell</b> (проще всего):\n"
    "1. Открой меню «Пуск» → набери <b>PowerShell</b> → Enter\n"
    "2. Вставь команду и нажми Enter:\n"
    "<pre>irm https://raw.githubusercontent.com/xynta/volodya-quiz/main/quiz.ps1 | iex</pre>\n"
    "<b>Командная строка (CMD):</b>\n"
    "<pre>powershell -NoProfile -ExecutionPolicy Bypass -Command \"irm https://raw.githubusercontent.com/xynta/volodya-quiz/main/quiz.ps1 | iex\"</pre>\n"
    "<b>Управление:</b> отвечай клавишами A/B/C/D. "
    "Подсказки: 1 — 50:50, 2 — помощь зала, 3 — звонок другу."
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
    bonus = prize_bonus_text(result.won, result.level_reached)
    bonus_block = f"\n\n🎁 {bonus}" if bonus else ""

    if result.won:
        return (
            "🎉 <b>ПОБЕДА!</b> Ты ответил(а) на все 15 вопросов!\n"
            f"🏆 Главный приз: <b>{result.final_prize}</b>"
            f"{bonus_block}\n\n"
            "Зал аплодирует стоя! 👏 Жми «Играть ещё», чтобы повторить."
        )
    if result.level_reached <= 0:
        body = "Ты не взял(а) ни одного уровня — но это только начало!"
    else:
        body = (
            f"Ты дошёл(ла) до уровня <b>{result.level_reached}</b> из 15.\n"
            f"Забираешь: <b>{result.final_prize}</b>"
        )
    return f"🏁 <b>Игра окончена.</b>\n{body}{bonus_block}\n\nПопробуем ещё раз?"


def _games_word(n: int) -> str:
    """Склонение слова «игра» по числу: 1 игру, 2 игры, 5 игр."""
    tens, units = n % 100, n % 10
    if units == 1 and tens != 11:
        return "игру"
    if 2 <= units <= 4 and not 12 <= tens <= 14:
        return "игры"
    return "игр"


def render_standing_note(standing: dict) -> str:
    """Короткая приписка после игры: личный итог игрока в общем зачёте."""
    total = format_rubles(standing["total"])
    games = standing["games"]
    return (
        f"\n\n💰 Всего унесено: <b>{total}</b> за {games} {_games_word(games)}\n"
        f"🏆 Место в зачёте: <b>№{standing['rank']}</b> из {standing['players']} — /top"
    )


_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _leaderboard_line(place: int, entry: dict, is_viewer: bool) -> str:
    marker = _MEDALS.get(place, f"{place}.")
    name = html.escape(entry.get("name") or "Без имени")
    me = "  ← ты" if is_viewer else ""
    return f"{marker} <b>{name}</b> — {format_rubles(entry['total'])}{me}"


def render_leaderboard(rows: list[dict], viewer_id: int, top_n: int = 10) -> str:
    """Текст лидерборда: топ-N игроков по сумме унесённых несгораемых сумм.
    Если зритель не попал в топ — его строка добавляется отдельно снизу."""
    if not rows:
        return (
            "🏆 <b>Лидерборд пуст</b>\n\n"
            "Пока никто не унёс ни рубля. Сыграй первым — жми «Играть»!"
        )

    viewer_key = str(viewer_id)
    lines = [
        "🏆 <b>Лидерборд</b>",
        "<i>Сумма всех несгораемых, что игроки унесли домой</i>",
        "",
    ]
    shown = rows[:top_n]
    for place, entry in enumerate(shown, start=1):
        lines.append(_leaderboard_line(place, entry, entry["user_id"] == viewer_key))

    if not any(e["user_id"] == viewer_key for e in shown):
        for place, entry in enumerate(rows, start=1):
            if entry["user_id"] == viewer_key:
                lines.append("…")
                lines.append(_leaderboard_line(place, entry, is_viewer=True))
                break

    return "\n".join(lines)
