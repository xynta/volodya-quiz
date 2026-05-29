"""Точка входа: запуск бота в режиме long-polling."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import require_bot_token
from handlers import setup_routers


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="play", description="Начать новую игру"),
        BotCommand(command="help", description="Как играть"),
        BotCommand(command="start", description="Перезапустить бота"),
    ])


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

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
