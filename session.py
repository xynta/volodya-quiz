"""Хранение состояния игры в FSM (MemoryStorage)."""
from aiogram.fsm.context import FSMContext

from game.engine import GameState

_KEY = "game"


async def save_game(ctx: FSMContext, game: GameState) -> None:
    await ctx.update_data(**{_KEY: game.to_dict()})


async def load_game(ctx: FSMContext) -> GameState | None:
    data = await ctx.get_data()
    raw = data.get(_KEY)
    return GameState.from_dict(raw) if raw else None
