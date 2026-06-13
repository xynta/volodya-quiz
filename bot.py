"""Точка входа: запуск бота в режиме long-polling."""
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BASE_DIR, require_bot_token
from handlers import setup_routers


def setup_logging() -> None:
    """INFO-логи в консоль и в файл с ротацией: 5 МБ × 3 бэкапа (потолок ≈20 МБ),
    чтобы лог не рос бесконечно. Файлы — в logs/ (вне гита)."""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                log_dir / "bot.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            ),
        ],
    )


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="play", description="Начать новую игру"),
        BotCommand(command="top", description="Лидерборд"),
        BotCommand(command="cmd", description="Запуск в консоли (PowerShell)"),
        BotCommand(command="help", description="Как играть"),
        BotCommand(command="start", description="Перезапустить бота"),
    ])


async def main() -> None:
    setup_logging()

    bot = Bot(token=require_bot_token(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_routers())

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
