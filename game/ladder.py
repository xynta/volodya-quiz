"""Помощники по призовой лесенке."""
from config import PRIZE_LADDER


def prize_for_level(level: int) -> str:
    """Приз на уровне (1-based). level=0 — игрок не взял ни одного."""
    if level <= 0:
        return "ничего"
    return PRIZE_LADDER[level - 1]["prize"]


def guaranteed_level(level: int) -> int:
    """Несгораемый уровень при провале на следующем вопросе.

    level — номер последнего ПРОЙДЕННОГО вопроса (1-based). Возвращает
    наивысший checkpoint, не превышающий level (0, если такого нет)."""
    guaranteed = 0
    for item in PRIZE_LADDER:
        if item["level"] <= level and item["is_checkpoint"]:
            guaranteed = item["level"]
    return guaranteed


def ladder_overview(current_level: int) -> str:
    """Текстовая лесенка с пометкой текущего уровня (1-based, какой сейчас
    разыгрывается). Несгораемые помечены 🔒."""
    lines = []
    for item in reversed(PRIZE_LADDER):
        lvl = item["level"]
        marker = "👉" if lvl == current_level else "  "
        lock = "🔒" if item["is_checkpoint"] else "  "
        lines.append(f"{marker} {lvl:>2}. {lock} {item['prize']}")
    return "\n".join(lines)
