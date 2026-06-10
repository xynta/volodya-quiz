"""Админ-команды: выдача собранных билдов доверенному пользователю.

Команда /builds скрыта из меню и доступна только пользователям из
config.ADMIN_USERNAMES (по умолчанию — @Ignodeau). Бот находит локальные
сборки консольной игры и присылает их файлами по кнопке."""
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from builds import discover_builds
from config import is_admin

router = Router()
logger = logging.getLogger(__name__)


def _fmt_date(mtime: float) -> str:
    return datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M")


@router.message(Command("builds"))
async def cmd_builds(message: Message) -> None:
    # Посторонним не отвечаем вовсе — команда остаётся «невидимой».
    if not is_admin(message.from_user.username):
        logger.info("Отказано в /builds пользователю @%s", message.from_user.username)
        return

    builds = discover_builds()
    if not builds:
        await message.answer(
            "📦 Готовых билдов не найдено.\n\n"
            "Собери их (<code>./build.sh</code>, <code>build.bat</code> или "
            "GitHub Actions) и положи рядом с ботом в папку <code>dist/</code> "
            "или <code>artifacts/</code>."
        )
        return

    lines = ["📦 <b>Доступные консольные сборки</b>:\n"]
    builder = InlineKeyboardBuilder()
    for i, b in enumerate(builds):
        lines.append(
            f"{i + 1}. {b['label']} — {b['size_h']}, {_fmt_date(b['mtime'])}\n"
            f"   <code>{b['location']}</code>"
        )
        builder.button(text=f"⬇️ {b['label']} ({b['size_h']})", callback_data=f"build:{i}")
    builder.adjust(1)
    await message.answer("\n".join(lines), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("build:"))
async def cb_build(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.username):
        await callback.answer("Нет доступа.", show_alert=True)
        return

    try:
        idx = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Не понял запрос.", show_alert=True)
        return

    builds = discover_builds()
    if idx < 0 or idx >= len(builds):
        await callback.answer("Список изменился. Набери /builds заново.", show_alert=True)
        return

    b = builds[idx]
    await callback.answer("Отправляю файл…")
    try:
        document = FSInputFile(b["path"], filename=b["path"].name)
        await callback.message.answer_document(
            document,
            caption=(
                f"{b['label']} · <code>{b['path'].name}</code>\n"
                f"{b['size_h']} · собрано {_fmt_date(b['mtime'])}"
            ),
        )
    except Exception:  # noqa: BLE001 — покажем пользователю и залогируем
        logger.exception("Не удалось отправить билд %s", b["path"])
        await callback.message.answer(
            "⚠️ Не получилось отправить файл (возможно, он слишком большой или "
            "недоступен). Подробности — в логах бота."
        )
