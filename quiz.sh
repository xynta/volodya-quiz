#!/usr/bin/env bash
# Консольная викторина «Кто хочет стать миллионером» (антураж «Званого ужина»)
# для macOS / Linux — запуск одной командой, без ручной установки.
#
# Запуск (Terminal на macOS, bash/zsh):
#   bash <(curl -fsSL https://raw.githubusercontent.com/xynta/volodya-quiz/main/quiz.sh)
#
# Скрипт скачивает репозиторий во временную папку и запускает Python-версию
# игры (console_quiz.py) с полным ASCII-оформлением. Нужен только python3 —
# сторонние пакеты не требуются. Временная папка удаляется по выходе из игры.
set -euo pipefail

REPO_TARBALL='https://codeload.github.com/xynta/volodya-quiz/tar.gz/main'

if ! command -v python3 >/dev/null 2>&1; then
    echo 'Нужен python3. На macOS установи Command Line Tools (xcode-select --install)' >&2
    echo 'или Python с python.org, затем повтори команду.' >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo 'Нужен curl (обычно он есть в системе по умолчанию).' >&2
    exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo '> Скачиваю викторину...'
curl -fsSL "$REPO_TARBALL" | tar xz -C "$tmp" --strip-components=1

cd "$tmp"
# console_quiz.py читает ввод с клавиатуры — стандартный stdin терминала
# (при запуске через bash <(...) он не занят, в отличие от curl | bash).
python3 console_quiz.py
