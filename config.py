"""Настройки игры и тематическая призовая лесенка."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


def require_bot_token() -> str:
    """Вернуть токен бота или упасть с понятной ошибкой.

    Проверка вынесена из момента импорта, чтобы консольную версию игры
    (console_quiz.py) можно было запускать без BOT_TOKEN — ей токен не нужен."""
    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Создай файл .env по образцу .env.example "
            "и положи туда токен от @BotFather."
        )
    return BOT_TOKEN

# Корень с ресурсами. В обычном запуске — папка проекта; внутри собранного
# PyInstaller-бинарника файлы лежат во временной папке sys._MEIPASS.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"

# Сколько вопросов в одной игре (классическая лесенка «Миллионера»).
QUESTIONS_PER_GAME = 15

# Количество подсказок (lifelines) на одну игру — по одной каждого типа.
# 50:50, «помощь зала», «звонок другу».

# Призовая лесенка в антураже «Званого ужина».
# is_checkpoint=True — несгораемый уровень: при ошибке после него
# игрок не падает в ноль, а сохраняет этот приз.
PRIZE_LADDER = [
    {"level": 1,  "prize": "Купон в «Азбуку Вкуса»",                          "is_checkpoint": False},
    {"level": 2,  "prize": "Рецепт салата-коктейля из Петрозаводска",         "is_checkpoint": False},
    {"level": 3,  "prize": "Порция мороженого в варёнке",                     "is_checkpoint": False},
    {"level": 4,  "prize": "Букет цветов от гостя Александра",                 "is_checkpoint": False},
    {"level": 5,  "prize": "Фоторамка от Владимира",                          "is_checkpoint": True},
    {"level": 6,  "prize": "Фирменная курица в вине со сливой",               "is_checkpoint": False},
    {"level": 7,  "prize": "Сувенирная неваляшка «не сдавайся»",              "is_checkpoint": False},
    {"level": 8,  "prize": "Таблица калорийности на кухню",                   "is_checkpoint": False},
    {"level": 9,  "prize": "Карта «40» от гостьи Леры",                       "is_checkpoint": False},
    {"level": 10, "prize": "150 баллов вечера и звание гостеприимной хозяйки", "is_checkpoint": True},
    {"level": 11, "prize": "Гастрольный тур с «Весёлыми девчатами-смешинками»", "is_checkpoint": False},
    {"level": 12, "prize": "Зажигательный финальный танец на бис",            "is_checkpoint": False},
    {"level": 13, "prize": "Эфир в прайм-тайм на РЕН ТВ",                     "is_checkpoint": False},
    {"level": 14, "prize": "Туристическая путёвка",                          "is_checkpoint": False},
    {"level": 15, "prize": "ГЛАВНЫЙ ПРИЗ — холодильник Gorenje с кристаллами Swarovski!", "is_checkpoint": False},
]
