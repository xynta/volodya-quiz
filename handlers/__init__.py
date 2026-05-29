"""Сбор всех роутеров."""
from aiogram import Router

from handlers.commands import router as commands_router
from handlers.quiz import router as quiz_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(commands_router)
    root.include_router(quiz_router)
    return root
