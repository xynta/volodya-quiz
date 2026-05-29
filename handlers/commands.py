"""Команды и старт игры."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from game.engine import new_game
from keyboards import play_keyboard, question_keyboard
from session import save_game
from states import Quiz
from texts import HELP, WELCOME, render_question

router = Router()


async def start_new_game(message: Message, ctx: FSMContext) -> None:
    """Создать игру, сохранить состояние и отправить первый вопрос."""
    game = new_game()
    await save_game(ctx, game)
    await ctx.set_state(Quiz.playing)
    await message.answer(render_question(game), reply_markup=question_keyboard(game))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=play_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP)


@router.message(Command("play"))
async def cmd_play(message: Message, state: FSMContext) -> None:
    await start_new_game(message, state)


@router.callback_query(F.data == "play")
async def cb_play(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await start_new_game(callback.message, state)
