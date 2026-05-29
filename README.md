# Викторина «Кто хочет стать миллионером» — «Званый ужин с Ольгой Стукаловой»

Квиз-лесенка из 15 вопросов по мотивам эпизода (РЕН ТВ): несгораемые уровни
5 и 10, три подсказки — 50:50, помощь зала, звонок другу.

Две версии с общим игровым ядром (`game/`):

- **Telegram-бот** — [bot.py](bot.py) (aiogram). Нужен `BOT_TOKEN` в `.env`.
- **Консольная версия в ASCII-стиле** — [console_quiz.py](console_quiz.py).
  Токен не нужен.

## Консоль — быстрый старт

```bash
python3 console_quiz.py
```

Управление: `A/B/C/D` — ответ, `50` / `зал` / `друг` — подсказки,
`л` — показать лесенку, `в` — выход.

## Сборка в исполняемый файл (без Python у игрока)

- **Windows (.exe):** двойной клик по [build.bat](build.bat) →
  `dist\stukalova_quiz.exe`
- **macOS / Linux:** `./build.sh` → `dist/stukalova_quiz`
- **Облачная сборка** обеих версий — GitHub Actions, вкладка *Actions*.

Подробности: [BUILD.md](BUILD.md).

## Telegram-бот

```bash
pip install -r requirements.txt
cp .env.example .env   # вписать BOT_TOKEN от @BotFather
python3 bot.py
```
