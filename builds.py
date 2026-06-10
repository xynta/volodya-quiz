"""Поиск собранных консольных билдов для выдачи через Telegram-бота.

Бот отдаёт готовые исполняемые файлы консольной игры (PyInstaller). Их кладут
в папки рядом с проектом: `dist/` (локальная сборка build.sh / build.bat) и
`artifacts/` (скачанные артефакты GitHub Actions). Этот модуль просто находит
такие файлы; раздачей и проверкой прав занимается handlers/admin.py."""
from pathlib import Path

from config import BASE_DIR

# Где искать готовые билды (относительно корня проекта).
_SEARCH_DIRS = ("dist", "artifacts")
# Имена консольных билдов без расширения (PyInstaller на macOS/Linux).
_CONSOLE_NAMES = ("volodya_quiz",)
# Расширения, которые однозначно считаем билдами (Windows / Android).
_BUILD_SUFFIXES = (".exe", ".apk")


def _is_build(path: Path) -> bool:
    return path.name in _CONSOLE_NAMES or path.suffix.lower() in _BUILD_SUFFIXES


def _platform_label(path: Path) -> str:
    suffix = path.suffix.lower()
    parent = path.parent.name.lower()
    if suffix == ".apk" or "android" in parent:
        return "🤖 Android (.apk)"
    if suffix == ".exe" or "windows" in parent or "win" in parent:
        return "🪟 Windows (.exe)"
    if "macos" in parent or "mac" in parent:
        return "🍎 macOS"
    return "🍎 macOS / 🐧 Linux"


def _human_size(num: int) -> str:
    size = float(num)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024 or unit == "ГБ":
            return f"{size:.0f} {unit}" if unit == "Б" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num} Б"


def discover_builds() -> list[dict]:
    """Найденные билды: список словарей {path, label, location, size, size_h,
    mtime}. Самые свежие — первыми. Дубли по абсолютному пути отсекаются."""
    seen: set[Path] = set()
    found: list[dict] = []
    for d in _SEARCH_DIRS:
        root = BASE_DIR / d
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or not _is_build(path):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            stat = path.stat()
            try:
                location = str(path.relative_to(BASE_DIR))
            except ValueError:
                location = str(path)
            found.append({
                "path": path,
                "label": _platform_label(path),
                "location": location,
                "size": stat.st_size,
                "size_h": _human_size(stat.st_size),
                "mtime": stat.st_mtime,
            })
    found.sort(key=lambda b: b["mtime"], reverse=True)
    return found
