#!/usr/bin/env python3
"""Консольная версия викторины «Кто хочет стать миллионером»
в антураже «Званого ужина с Ольгой Стукаловой» — в ASCII-стиле.

Переиспользует игровое ядро Telegram-бота (game/*, config.py),
но всё взаимодействие идёт через терминал: рамки, ASCII-арт,
ввод с клавиатуры. Токен бота не требуется.

Запуск:  python3 console_quiz.py
"""
import atexit
import os
import sys
import time

from config import PRIZE_LADDER, QUESTIONS_PER_GAME
from game.engine import new_game, answer
from game.ladder import guaranteed_level, prize_for_level
from game.lifelines import audience_help, fifty_fifty, friend_call

FROZEN = getattr(sys, "frozen", False)  # запущены как собранный exe/бинарник


def _enable_windows_ansi() -> bool:
    """Включить обработку ANSI-кодов в консоли Windows 10+.

    Без этого собранный .exe в cmd.exe печатал бы escape-последовательности
    как мусор. На не-Windows просто возвращает True."""
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # 7 = ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP_AT_EOL | VT_PROCESSING
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        # Кириллица в старых консолях — переключаем кодовую страницу на UTF-8.
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
        return True
    except Exception:
        return False


_ANSI_OK = _enable_windows_ansi()

# ────────────────────────────── оформление ──────────────────────────────

W = 64  # ширина «холста» между рамками |...|

USE_COLOR = _ANSI_OK and sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def _c(code):
    """Вернуть функцию-раскраску для ANSI-кода (или пустышку без цвета)."""
    def paint(text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if USE_COLOR else text
    return paint


BOLD = _c("1")
DIM = _c("2")
GREEN = _c("1;32")
RED = _c("1;31")
YELLOW = _c("1;33")
CYAN = _c("1;36")
GOLD = _c("33")
MAGENTA = _c("1;35")


def clear() -> None:
    if USE_COLOR:
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" * 2)


def hr(ch: str = "=") -> str:
    return "+" + ch * W + "+"


def row(text: str = "", color=None, indent: int = 2) -> str:
    """Одна строка внутри рамки, дополненная пробелами до ширины W."""
    content = " " * indent + text
    if len(content) > W:
        content = content[:W]
    content += " " * (W - len(content))
    if color:
        content = color(content)
    return "|" + content + "|"


def row_center(text: str, color=None) -> str:
    pad = max(0, (W - len(text)) // 2)
    return row(" " * (pad - 2 if pad >= 2 else 0) + text, color=color)


def wrap(text: str, width: int) -> list[str]:
    """Простой перенос по словам (textwrap корректно считает кириллицу,
    но обойдёмся без зависимости)."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        if len(cur) + len(word) + (1 if cur else 0) <= width:
            cur = f"{cur} {word}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


# ────────────────────────────── баннер ──────────────────────────────

BANNER = r"""
   ___  _   _ ___ _____
  / _ \| | | |_ _|__  /
 | | | | | | || |  / /
 | |_| | |_| || | / /_
  \__\_\\___/|___/____|
"""


def show_intro() -> None:
    clear()
    print(YELLOW(hr("=")))
    for line in BANNER.strip("\n").splitlines():
        print(YELLOW(row_center(line)))
    print(YELLOW(hr("=")))
    print(row_center(BOLD("КТО ХОЧЕТ СТАТЬ МИЛЛИОНЕРОМ")))
    print(row_center(DIM("~ Званый ужин с Ольгой Стукаловой (РЕН ТВ) ~")))
    print(hr("-"))
    body = (
        "Перед тобой лесенка из 15 вопросов — от простых до каверзных. "
        "Один неверный ответ завершает игру, но на 5-м и 10-м уровнях "
        "есть несгораемые призы [*]. В запасе три подсказки: 50:50, "
        "помощь зала и звонок другу."
    )
    for line in wrap(body, W - 4):
        print(row(line))
    print(row())
    print(row("Готов(а) сесть за стол?", color=BOLD))
    print(hr("="))
    input(DIM("   Нажми Enter, чтобы начать игру... "))


# ────────────────────────────── лесенка ──────────────────────────────

def render_ladder(current_level: int) -> None:
    print(hr("="))
    print(row_center(BOLD("ПРИЗОВАЯ ЛЕСЕНКА")))
    print(hr("-"))
    limit = W - 2  # запас под отступ строки (indent=2)
    for item in reversed(PRIZE_LADDER):
        lvl = item["level"]
        marker = ">>" if lvl == current_level else "  "
        lock = "[*]" if item["is_checkpoint"] else "   "
        text = f"{marker} {lvl:>2}. {lock} {item['prize']}"
        if len(text) > limit:
            text = text[: limit - 2].rstrip() + ".."
        if lvl == current_level:
            print(row(text, color=YELLOW))
        elif item["is_checkpoint"]:
            print(row(text, color=CYAN))
        else:
            print(row(text))
    print(hr("="))
    print(DIM("   [*] — несгораемый уровень. >> — текущий вопрос."))


# ────────────────────────────── вопрос ──────────────────────────────

def render_question(game) -> None:
    clear()
    level = game.level
    guaranteed = guaranteed_level(level - 1)
    guaranteed_txt = prize_for_level(guaranteed) if guaranteed else "—"
    q = game.current

    print(MAGENTA(hr("=")))
    print(MAGENTA(row(f"Вопрос {level} из {QUESTIONS_PER_GAME}", color=BOLD)))
    for line in wrap(f"Играем за: {prize_for_level(level)}", W - 4):
        print(row(line, color=GOLD))
    for line in wrap(f"Несгораемое: {guaranteed_txt}", W - 4):
        print(row(line, color=CYAN))
    print(MAGENTA(hr("-")))

    for line in wrap(q["question"], W - 4):
        print(row(line, color=BOLD))
    print(row())

    for letter in game.available_letters():
        for i, line in enumerate(wrap(f"{letter}) {q['options'][letter]}", W - 6)):
            print(row(("   " if i else " ") + line))
    print(MAGENTA(hr("=")))


# ────────────────────────────── подсказки ──────────────────────────────

def show_audience(votes: dict) -> None:
    bar_len = 24
    print(hr("="))
    print(row(BOLD("ПОМОЩЬ ЗАЛА"), indent=2))
    print(hr("-"))
    for letter in sorted(votes):
        pct = votes[letter]
        filled = round(pct / 100 * bar_len)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(row(f"{letter} |{bar}| {pct:>3}%"))
    print(hr("="))


def show_friend(text: str) -> None:
    print(hr("="))
    print(row(BOLD("ЗВОНОК ДРУГУ  *звонит телефон*"), indent=2))
    print(hr("-"))
    for line in wrap(f'— {text}', W - 4):
        print(row(line, color=CYAN))
    print(hr("="))


# ────────────────────────────── итоги ──────────────────────────────

def show_reveal(question: dict, result) -> None:
    print()
    print(DIM("   Проверяю ответ..."), flush=True)
    time.sleep(0.9)
    print(hr("="))
    if result.correct:
        print(row(f"[ВЕРНО!] {result.chosen}) {question['options'][result.chosen]}"[: W - 2],
                  color=GREEN))
        print(row(f"Забрано: {result.final_prize}"[: W - 2], color=GOLD))
    else:
        ct = question["options"][result.correct_letter]
        print(row(f"[УВЫ, НЕВЕРНО] Ты выбрал(а): {result.chosen}"[: W - 2], color=RED))
        print(row(f"Правильный ответ: {result.correct_letter}) {ct}"[: W - 2], color=BOLD))
    print(hr("="))
    if not result.finished:
        input(DIM("   Enter — следующий вопрос... "))


def show_game_over(result) -> None:
    clear()
    if result.won:
        print(GOLD(hr("=")))
        for line in [
            "  $$$   ПОБЕДА!   $$$",
            "",
            "Ты ответил(а) на все 15 вопросов!",
        ]:
            print(GOLD(row_center(line)) if line.strip() else row())
        print(hr("-"))
        for line in wrap(f"ГЛАВНЫЙ ПРИЗ: {result.final_prize}", W - 4):
            print(row(line, color=GOLD))
        print(row())
        print(row("Ольга Стукалова аплодирует стоя!  \\o/", color=BOLD))
        print(GOLD(hr("=")))
        return

    print(RED(hr("=")))
    print(RED(row_center(BOLD("ИГРА ОКОНЧЕНА"))))
    print(hr("-"))
    if result.level_reached <= 0:
        print(row("Ты не взял(а) ни одного уровня — но это только начало!"))
    else:
        print(row(f"Ты дошёл(ла) до уровня {result.level_reached} из 15."))
        for line in wrap(f"Забираешь: {result.final_prize}", W - 4):
            print(row(line, color=GOLD))
    print(RED(hr("=")))


# ────────────────────────────── ввод ──────────────────────────────

ANSWER_KEYS = {"a", "b", "c", "d", "а", "в", "с", "д"}
# кириллические двойники → латиница (на случай раскладки)
CYR_MAP = {"а": "A", "в": "B", "с": "C", "д": "D"}


def read_command(game) -> str:
    """Показать подсказку по командам и вернуть нормализованный ввод."""
    opts = ["A/B/C/D — ответ"]
    if not game.lifelines["fifty"]:
        opts.append("50")
    if not game.lifelines["audience"]:
        opts.append("зал")
    if not game.lifelines["friend"]:
        opts.append("друг")
    opts += ["л — лесенка", "в — выход"]
    print(DIM("   Команды: " + " | ".join(opts)))
    try:
        return input(BOLD("   Твой ход: ")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "в"


# ────────────────────────────── игровой цикл ──────────────────────────────

def play_one_game() -> None:
    game = new_game()
    render_question(game)

    while not game.finished:
        cmd = read_command(game)

        # — выход —
        if cmd in ("в", "q", "выход", "exit", "quit"):
            print(DIM("\n   Выходим из-за стола. До встречи!\n"))
            sys.exit(0)

        # — лесенка —
        if cmd in ("л", "l", "лесенка"):
            render_question(game)
            render_ladder(game.level)
            continue

        # — подсказки —
        if cmd in ("50", "5050", "50:50") and not game.lifelines["fifty"]:
            game.lifelines["fifty"] = True
            to_hide = fifty_fifty(game.current, game.hidden)
            game.hidden = list(set(game.hidden) | set(to_hide))
            render_question(game)
            print(YELLOW("   50:50 — убрали два неверных варианта!"))
            continue

        if cmd in ("зал", "z", "зл", "помощь") and not game.lifelines["audience"]:
            game.lifelines["audience"] = True
            votes = audience_help(game.current, game.hidden)
            render_question(game)
            show_audience(votes)
            continue

        if cmd in ("друг", "d", "др", "звонок") and not game.lifelines["friend"]:
            game.lifelines["friend"] = True
            render_question(game)
            show_friend(friend_call(game.current, game.hidden))
            continue

        # — ответ —
        letter = CYR_MAP.get(cmd, cmd.upper())
        if letter in ("A", "B", "C", "D"):
            if letter not in game.available_letters():
                print(RED("   Этого варианта уже нет (убран подсказкой 50:50)."))
                continue
            question = game.current  # фиксируем до перехода
            result = answer(game, letter)
            show_reveal(question, result)
            if result.finished:
                show_game_over(result)
            else:
                render_question(game)
            continue

        # — непонятный ввод —
        print(RED("   Не понял команду. Нажми A/B/C/D или используй подсказку."))


def main() -> None:
    show_intro()
    while True:
        play_one_game()
        try:
            again = input(BOLD("\n   Сыграем ещё? (д/н): ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            again = "н"
        if again not in ("д", "y", "да", "yes", "ещё", "еще"):
            print(DIM("\n   Спасибо за игру! Заходите на «Званый ужин» ещё.\n"))
            break


def _pause_before_close() -> None:
    """Чтобы окно собранного .exe не захлопывалось мгновенно по двойному клику."""
    if FROZEN:
        try:
            input(DIM("\n   Нажми Enter, чтобы закрыть окно... "))
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    atexit.register(_pause_before_close)
    main()
