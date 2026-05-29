# Сборка консольного квиза в исполняемый файл

Консольная игра ([console_quiz.py](console_quiz.py)) упаковывается в один
самодостаточный файл — Python на машине игрока не нужен. Вопросы
(`data/questions.json`) встраиваются внутрь.

## macOS (собрать прямо здесь)

```bash
./build.sh
```

Результат: `dist/stukalova_quiz`. Запуск — двойным кликом или из терминала:

```bash
./dist/stukalova_quiz
```

> Это не `.exe` (у macOS другой формат), но смысл тот же — запуск без Python.
> При первом открытии двойным кликом macOS может спросить разрешение:
> правый клик → «Открыть» → «Открыть».

## Windows (.exe)

`.exe` нельзя собрать на Mac напрямую — нужна Windows. Два пути:

### Вариант А — облачная сборка через GitHub Actions (без своей Windows)

1. Создай репозиторий на GitHub и запушь проект:
   ```bash
   git init && git add . && git commit -m "console quiz + build"
   git branch -M main
   git remote add origin <URL-репозитория>
   git push -u origin main
   ```
2. На GitHub: вкладка **Actions** → workflow **«Сборка консольного квиза»**
   → **Run workflow**. (Он также запускается сам при пуше в `main`.)
3. Когда сборка закончится, скачай артефакт **`stukalova_quiz-windows`** —
   внутри готовый `stukalova_quiz.exe`. Заодно соберётся и macOS-версия
   (`stukalova_quiz-macos`).

Конфигурация: [.github/workflows/build.yml](.github/workflows/build.yml).

### Вариант Б — на Windows-машине

Поставь Python 3.11+ и запусти из папки проекта:

```bat
build.bat
```

Результат: `dist\stukalova_quiz.exe`.

## Как это устроено

- Сборка управляется spec-файлом [stukalova_quiz.spec](stukalova_quiz.spec)
  (одинаков для всех ОС, разделители путей внутри от системы не зависят).
- Aiogram и сетевая обвязка бота из консольной сборки исключены — бинарник
  компактнее.
- Зависимости сборки — [requirements-build.txt](requirements-build.txt).
