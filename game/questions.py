"""Загрузка вопросов и формирование набора на одну игру."""
import json
import random
from collections import defaultdict

from config import DAYS, QUESTIONS_PATH, QUESTIONS_PER_GAME

with open(QUESTIONS_PATH, encoding="utf-8") as f:
    ALL_QUESTIONS = json.load(f)

# Группируем вопросы по (день, уровень): {(1, 1): [3 варианта], ...}
_BY_DAY_SET = defaultdict(list)
for _q in ALL_QUESTIONS:
    _BY_DAY_SET[(_q["day"], _q["set"])].append(_q)

# Доступные дни (вечера), которые реально есть в данных.
AVAILABLE_DAYS = sorted({d for (d, _s) in _BY_DAY_SET})


def random_day() -> int:
    """Случайный вечер из числа описанных в config.DAYS и присутствующих
    в данных."""
    days = [d["day"] for d in DAYS if d["day"] in AVAILABLE_DAYS] or AVAILABLE_DAYS
    return random.choice(days)


def build_game_questions(day: int):
    """Собрать вопросы на одну игру для конкретного вечера: по одному
    случайному варианту из каждого уровня, в порядке уровней (нарастающая
    сложность)."""
    sets = sorted(s for (d, s) in _BY_DAY_SET if d == day)
    chosen = [random.choice(_BY_DAY_SET[(day, s)]) for s in sets]
    return chosen[:QUESTIONS_PER_GAME]
