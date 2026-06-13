"""Персистентный лидерборд: сумма унесённых несгораемых сумм по игрокам.

Идея концепта: за каждую игру игрок уносит домой несгораемую сумму — то, что
реально забрал на момент окончания (проигрыш → последний несгораемый уровень,
победа → главный приз). Лидерборд складывает эти суммы по всем играм игрока,
и кто унёс больше рублей суммарно — тот выше.

Хранится в JSON-файле (config.LEADERBOARD_PATH), переживает перезапуск бота.
Ключ записи — Telegram user id (стабилен), имя — отображаемое имя из Telegram
(обновляется на актуальное при каждой игре).
"""
import json
import logging
import os
import tempfile
import threading
from pathlib import Path

from config import LEADERBOARD_PATH

logger = logging.getLogger(__name__)

# Бот работает в одном потоке (asyncio), но record_game делает
# read-modify-write файла; лок защищает от гонок, если когда-нибудь появятся
# потоки, а атомарная запись — от битого файла при сбое.
_lock = threading.Lock()


def _load() -> dict:
    """Прочитать лидерборд из файла. Любая проблема чтения → пустой словарь
    (не роняем бота из-за повреждённого/отсутствующего файла)."""
    try:
        with open(LEADERBOARD_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        logger.exception("Не удалось прочитать лидерборд %s — считаю пустым", LEADERBOARD_PATH)
        return {}


def _save(data: dict) -> None:
    """Атомарно записать лидерборд: пишем во временный файл рядом и заменяем
    исходный одним системным вызовом (os.replace), чтобы не получить
    полузаписанный JSON при падении."""
    path = Path(LEADERBOARD_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".lb-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:  # noqa: BLE001 — не роняем бота из-за сбоя записи (OSError
        # при I/O, ValueError/TypeError при сериализации); просто логируем.
        logger.exception("Не удалось сохранить лидерборд %s", path)
    finally:
        # Если os.replace отработал, tmp уже переименован и не существует —
        # иначе подчищаем временный файл, чтобы не копить .lb-*.tmp.
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def _new_entry(name: str) -> dict:
    return {"name": name, "total": 0, "games": 0, "best": 0, "wins": 0}


def _ranked(data: dict) -> list[dict]:
    """Список записей, отсортированный для лидерборда: больше суммы → выше;
    при равной сумме выше тот, кто добился её за меньшее число игр; затем по
    имени — для стабильного порядка. В каждую запись добавлен user_id."""
    items = [{"user_id": uid, **entry} for uid, entry in data.items()]
    items.sort(key=lambda e: (-int(e["total"]), int(e["games"]), str(e["name"]).lower()))
    return items


def record_game(user_id: int, name: str, amount: int, won: bool = False) -> dict:
    """Записать итог завершённой игры и вернуть актуальную статистику игрока.

    amount — унесённая несгораемая сумма в рублях (>=0; 0, если не взял ни
    одного несгораемого уровня). Возвращает словарь с полями записи плюс
    rank (место, 1-based) и players (всего игроков) — для показа после игры.
    """
    amount = max(0, int(amount))
    with _lock:
        data = _load()
        key = str(user_id)
        entry = data.get(key) or _new_entry(name)
        entry["name"] = name or entry.get("name") or "Без имени"
        entry["total"] = int(entry.get("total", 0)) + amount
        entry["games"] = int(entry.get("games", 0)) + 1
        entry["best"] = max(int(entry.get("best", 0)), amount)
        if won:
            entry["wins"] = int(entry.get("wins", 0)) + 1
        data[key] = entry
        _save(data)

        ranked = _ranked(data)
        rank = next(i for i, e in enumerate(ranked, start=1) if e["user_id"] == key)
        return {**entry, "user_id": key, "rank": rank, "players": len(data)}


def ranked() -> list[dict]:
    """Все игроки в порядке лидерборда (см. _ranked). Каждая запись содержит
    user_id, name, total, games, best, wins."""
    return _ranked(_load())
