#!/usr/bin/env bash
# Сборка консольного квиза в один файл на macOS / Linux.
# Результат: dist/volodya_quiz
set -e
cd "$(dirname "$0")"

python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller volodya_quiz.spec --noconfirm --clean

echo
echo "Готово! Запуск:  ./dist/volodya_quiz"
