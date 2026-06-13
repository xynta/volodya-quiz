"""Команда лидерборда: топ игроков по сумме унесённых несгораемых сумм."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import play_keyboard
from leaderboard import ranked
from texts import render_leaderboard

router = Router()

TOP_N = 10


async def _send_leaderboard(message: Message, viewer_id: int) -> None:
    rows = ranked()
    await message.answer(
        render_leaderboard(rows, viewer_id, TOP_N), reply_markup=play_keyboard()
    )


@router.message(Command("top", "leaderboard"))
async def cmd_top(message: Message) -> None:
    await _send_leaderboard(message, message.from_user.id)


@router.callback_query(F.data == "leaderboard")
async def cb_leaderboard(callback: CallbackQuery) -> None:
    await callback.answer()
    # viewer_id — тот, кто нажал кнопку (а не владелец сообщения-бота).
    await _send_leaderboard(callback.message, callback.from_user.id)
