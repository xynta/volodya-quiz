"""Настройки игры и тематическая призовая лесенка."""
import os
import sys
from pathlib import Path

# python-dotenv нужен только боту (читает BOT_TOKEN из .env). Консольной
# версии (console_quiz.py) он не требуется, поэтому импорт необязательный —
# иначе игру нельзя было бы запустить на чистом stdlib (например, при запуске
# одной командой на macOS/Linux без установки зависимостей).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass

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


# Имена пользователей Telegram (без @), которым доступны админ-команды бота —
# например, скачивание собранных билдов через /builds. По умолчанию — @Ignodeau
# и @Pj_301m. Можно переопределить переменной окружения ADMIN_USERNAMES
# (через запятую) — тогда дефолт игнорируется.
ADMIN_USERNAMES = {
    u.strip().lstrip("@").lower()
    for u in os.getenv("ADMIN_USERNAMES", "Ignodeau,Pj_301m").split(",")
    if u.strip()
}


def is_admin(username: str | None) -> bool:
    """Разрешён ли пользователю доступ к админ-командам (по username)."""
    return bool(username) and username.lower() in ADMIN_USERNAMES


# Корень с ресурсами. В обычном запуске — папка проекта; внутри собранного
# PyInstaller-бинарника файлы лежат во временной папке sys._MEIPASS.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = BASE_DIR / "data" / "questions.json"

# Файл с лидербордом (сумма унесённых несгораемых по игрокам). Хранится вне
# гита и переживает перезапуск бота. Путь можно переопределить переменной
# окружения LEADERBOARD_PATH — например, чтобы положить его на постоянный диск.
LEADERBOARD_PATH = Path(os.getenv("LEADERBOARD_PATH") or BASE_DIR / "data" / "leaderboard.json")

# Сколько вопросов в одной игре (классическая лесенка «Миллионера»).
QUESTIONS_PER_GAME = 15

# Количество подсказок (lifelines) на одну игру — по одной каждого типа.
# 50:50, «помощь зала», «звонок другу».

# Вечера недели «Званого ужина». Каждый день — отдельная викторина из 15
# уровней (по 3 варианта вопроса на уровень). В начале игры вечер выбирается
# случайно. Поле "day" совпадает с полем "day" в data/questions.json.
DAYS = [
    {"day": 1, "weekday": "понедельник", "host": "Ольга Стукалова"},
    {"day": 2, "weekday": "вторник",     "host": "Александр Асиновский"},
    {"day": 3, "weekday": "среда",       "host": "Лера Гаврилова"},
    {"day": 4, "weekday": "четверг",     "host": "Владимир Чони"},
    {"day": 5, "weekday": "пятница",     "host": "Владимир Алексеев"},
]


def day_info(day: int) -> dict:
    """Метаданные вечера по его номеру (1–5)."""
    for item in DAYS:
        if item["day"] == day:
            return item
    return {"day": day, "weekday": "?", "host": "?"}


# Денежная призовая лесенка «Кто хочет стать миллионером» (рубли).
# is_checkpoint=True — несгораемый уровень: при ошибке после него игрок
# не падает в ноль, а сохраняет этот приз. Несгораемые — 1 000 ₽ (ур. 5)
# и 32 000 ₽ (ур. 10), как в спецификации призов.
# Поле "amount" — та же сумма числом (рубли), нужна для лидерборда: лесенка
# хранит приз текстом, а считать суммы удобнее по числам (см. game/ladder.py).
PRIZE_LADDER = [
    {"level": 1,  "prize": "100 рублей",       "amount": 100,       "is_checkpoint": False},
    {"level": 2,  "prize": "200 рублей",       "amount": 200,       "is_checkpoint": False},
    {"level": 3,  "prize": "300 рублей",       "amount": 300,       "is_checkpoint": False},
    {"level": 4,  "prize": "500 рублей",       "amount": 500,       "is_checkpoint": False},
    {"level": 5,  "prize": "1 000 рублей",     "amount": 1000,      "is_checkpoint": True},
    {"level": 6,  "prize": "2 000 рублей",     "amount": 2000,      "is_checkpoint": False},
    {"level": 7,  "prize": "4 000 рублей",     "amount": 4000,      "is_checkpoint": False},
    {"level": 8,  "prize": "8 000 рублей",     "amount": 8000,      "is_checkpoint": False},
    {"level": 9,  "prize": "16 000 рублей",    "amount": 16000,     "is_checkpoint": False},
    {"level": 10, "prize": "32 000 рублей",    "amount": 32000,     "is_checkpoint": True},
    {"level": 11, "prize": "64 000 рублей",    "amount": 64000,     "is_checkpoint": False},
    {"level": 12, "prize": "125 000 рублей",   "amount": 125000,    "is_checkpoint": False},
    {"level": 13, "prize": "250 000 рублей",   "amount": 250000,    "is_checkpoint": False},
    {"level": 14, "prize": "500 000 рублей",   "amount": 500000,    "is_checkpoint": False},
    {"level": 15, "prize": "1 000 000 рублей", "amount": 1000000,   "is_checkpoint": False},
]

# Тексты призов из спецификации. Показываются на экране окончания игры
# в зависимости от достигнутого несгораемого уровня (см. game/ladder.py).

# Несгораемое на 5-м уровне (1 000 ₽).
PRIZE_5_TEXT = (
    "Вы выиграли тысячу рублей. В подарок мудрость от Владимира Алексеева: "
    "кто ходит в гости по утрам, тот поступает мудро, то тут сто грамм, "
    "то там сто грамм, на то оно и утро!"
)

# Несгораемое на 10-м уровне (32 000 ₽).
PRIZE_10_TEXT = (
    "Вы выиграли 32 тысячи рублей и рецепт сникерса по-украински:\n"
    "1. Кусочек чёрного хлебушка\n"
    "2. Кусочек сала\n"
    "3. Сверху плиточка шоколада\n"
    "4. Сало плавится, шоколад тает\n"
    "5. И получается сникерс по-украински"
)

# Суперприз за все 15 вопросов (1 000 000 ₽).
PRIZE_15_TEXT = (
    "Вы выиграли суперприз, один миллион рублей!\n\n"
    "Ссылка на все выпуски Званого Ужина с Владимиром Алексеевым:\n"
    "https://drive.google.com/file/d/1OZMruBVEoAnP8j3Z7rr0b2PEDNbj7wzY/view\n\n"
    "Ссылка на нарративную новеллу по Званому Ужину с Владимиром Алексеевым:\n"
    "https://locator101.itch.io/dinner\n\n"
    "Ссылка на группу VK, посвящённую этому выпуску:\n"
    "https://vk.ru/zvanyi_uzhin"
)
