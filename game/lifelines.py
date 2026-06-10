"""Подсказки: 50:50, помощь зала, звонок другу.

Все функции принимают текущий вопрос (dict) и опционально список уже скрытых
вариантов, возвращают данные для отображения. Перекос делается в сторону
правильного ответа, чтобы подсказки были полезными, но не стопроцентными."""
import random

LETTERS = ["A", "B", "C", "D"]


def fifty_fifty(question: dict, hidden: list[str] | None = None) -> list[str]:
    """Вернуть список из двух букв, которые нужно скрыть: правильный ответ
    остаётся, плюс один случайный неверный."""
    correct = question["correct"]
    wrong = [l for l in LETTERS if l != correct]
    keep_wrong = random.choice(wrong)
    return [l for l in wrong if l != keep_wrong]


def audience_help(question: dict, hidden: list[str] | None = None) -> dict[str, int]:
    """Распределение голосов зала по процентам. Перекос в сторону правильного.
    Скрытые варианты (после 50:50) исключаются."""
    hidden = hidden or []
    available = [l for l in LETTERS if l not in hidden]
    correct = question["correct"]

    # Правильному даём заметное преимущество, остальное делим случайно.
    correct_share = random.randint(45, 70)
    rest = [l for l in available if l != correct]
    remaining = 100 - correct_share

    votes = {correct: correct_share}
    if rest:
        cuts = sorted(random.sample(range(0, remaining + 1), len(rest) - 1)) if len(rest) > 1 else []
        bounds = [0] + cuts + [remaining]
        for i, letter in enumerate(rest):
            votes[letter] = bounds[i + 1] - bounds[i]
    # Округление могло «потерять» проценты — добросим правильному.
    diff = 100 - sum(votes.values())
    votes[correct] += diff
    return votes


# Канонические ответы друга из спецификации. Друг бесполезен и отвечает
# невпопад — никакой реальной подсказки, чистый юмор передачи.
_FRIEND_ANSWERS = [
    "Выбирайте что хотите, как хотите, хоть усритесь.",
    "Посмотри в компьютере. Сейчас ведь куда ни посмотри, везде компьютер.",
    "В этой викторине нужны образованные люди.",
    "Опупенно, бомбенно, бумбумба!",
]


def friend_call(question: dict, hidden: list[str] | None = None) -> str:
    """Текст «звонка другу» — один из канонических ответов наугад.
    Аргументы question/hidden оставлены для совместимости интерфейса."""
    return random.choice(_FRIEND_ANSWERS)
