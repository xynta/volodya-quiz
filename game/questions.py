"""Загрузка вопросов и формирование набора на одну игру."""
import json
import random
from collections import defaultdict

from config import QUESTIONS_PATH, QUESTIONS_PER_GAME

with open(QUESTIONS_PATH, encoding="utf-8") as f:
    ALL_QUESTIONS = json.load(f)

# Группируем вопросы по наборам: {1: [...], 2: [...], ...}
_BY_SET = defaultdict(list)
for _q in ALL_QUESTIONS:
    _BY_SET[_q["set"]].append(_q)

SETS = sorted(_BY_SET.keys())


def build_game_questions():
    """Собрать вопросы на одну игру: по одному случайному из каждого набора,
    в порядке наборов (нарастающая сложность). Если наборов больше, чем нужно
    вопросов — берём первые QUESTIONS_PER_GAME; если меньше — добираем случайно."""
    chosen = [random.choice(_BY_SET[s]) for s in SETS]

    if len(chosen) >= QUESTIONS_PER_GAME:
        return chosen[:QUESTIONS_PER_GAME]

    # Наборов меньше, чем нужно вопросов — добираем случайными из общего пула.
    pool = [q for q in ALL_QUESTIONS if q not in chosen]
    random.shuffle(pool)
    return chosen + pool[: QUESTIONS_PER_GAME - len(chosen)]
