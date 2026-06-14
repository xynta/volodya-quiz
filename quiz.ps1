# Консольная викторина «Кто хочет стать миллионером»
# в антураже «Званого ужина» — чистый PowerShell, без установок.
#
# Запуск одной командой (PowerShell):
#   irm https://raw.githubusercontent.com/xynta/volodya-quiz/main/quiz.ps1 | iex
#
# Скрипт сам скачивает вопросы из data/questions.json того же репозитория,
# так что вопросы не дублируются — единый источник правды с Telegram-ботом.

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
# На старых Windows PowerShell 5.1 запрос к GitHub без TLS 1.2 падает.
try {
    [Net.ServicePointManager]::SecurityProtocol =
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {}

$REPO_RAW      = 'https://raw.githubusercontent.com/xynta/volodya-quiz/main'
$QUESTIONS_URL = "$REPO_RAW/data/questions.json"
$QUESTIONS_PER_GAME = 15
$W = 64   # ширина «холста» между рамками |...|

# ── Денежная лесенка (несгораемые — уровни 5 и 10) ───────────────────────
$PRIZE_LADDER = @(
    @{ level = 1;  prize = '100 рублей';       checkpoint = $false }
    @{ level = 2;  prize = '200 рублей';       checkpoint = $false }
    @{ level = 3;  prize = '300 рублей';       checkpoint = $false }
    @{ level = 4;  prize = '500 рублей';       checkpoint = $false }
    @{ level = 5;  prize = '1 000 рублей';     checkpoint = $true  }
    @{ level = 6;  prize = '2 000 рублей';     checkpoint = $false }
    @{ level = 7;  prize = '4 000 рублей';     checkpoint = $false }
    @{ level = 8;  prize = '8 000 рублей';     checkpoint = $false }
    @{ level = 9;  prize = '16 000 рублей';    checkpoint = $false }
    @{ level = 10; prize = '32 000 рублей';    checkpoint = $true  }
    @{ level = 11; prize = '64 000 рублей';    checkpoint = $false }
    @{ level = 12; prize = '125 000 рублей';   checkpoint = $false }
    @{ level = 13; prize = '250 000 рублей';   checkpoint = $false }
    @{ level = 14; prize = '500 000 рублей';   checkpoint = $false }
    @{ level = 15; prize = '1 000 000 рублей'; checkpoint = $false }
)

$DAYS = @{
    1 = @{ weekday = 'понедельник'; host = 'Ольга Стукалова'     }
    2 = @{ weekday = 'вторник';     host = 'Александр Асиновский' }
    3 = @{ weekday = 'среда';       host = 'Лера Гаврилова'       }
    4 = @{ weekday = 'четверг';     host = 'Владимир Чони'        }
    5 = @{ weekday = 'пятница';     host = 'Владимир Алексеев'    }
}

# ── Призовые тексты из спецификации ──────────────────────────────────────
$PRIZE_5_TEXT = @'
Вы выиграли тысячу рублей. В подарок мудрость от Владимира Алексеева:
кто ходит в гости по утрам, тот поступает мудро, то тут сто грамм,
то там сто грамм, на то оно и утро!
'@

$PRIZE_10_TEXT = @'
Вы выиграли 32 тысячи рублей и рецепт сникерса по-украински:
  1. Кусочек чёрного хлебушка
  2. Кусочек сала
  3. Сверху плиточка шоколада
  4. Сало плавится, шоколад тает
  5. И получается сникерс по-украински
'@

$PRIZE_15_TEXT = @'
Вы выиграли суперприз, один миллион рублей!

Все выпуски Званого Ужина с Владимиром Алексеевым:
  https://drive.google.com/file/d/1OZMruBVEoAnP8j3Z7rr0b2PEDNbj7wzY/view

Нарративная новелла по Званому Ужину:
  https://locator101.itch.io/dinner

Группа VK, посвящённая этому выпуску:
  https://vk.ru/zvanyi_uzhin
'@

$FRIEND_ANSWERS = @(
    'Выбирайте что хотите, как хотите, хоть усритесь.'
    'Посмотри в компьютере. Сейчас ведь куда ни посмотри, везде компьютер.'
    'В этой викторине нужны образованные люди.'
    'Опупенно, бомбенно, бумбумба!'
)

$LETTERS = @('A', 'B', 'C', 'D')

# ── Хелперы оформления (рамки, центрирование, перенос) ────────────────────
function Hr {
    param([string]$ch = '=')
    return '+' + ($ch * $W) + '+'
}

function Row {
    param([string]$text = '', [int]$indent = 2)
    $content = (' ' * $indent) + $text
    if ($content.Length -gt $W) { $content = $content.Substring(0, $W) }
    return '|' + $content.PadRight($W) + '|'
}

function Row-Center {
    param([string]$text)
    $pad = [Math]::Max(0, [int][Math]::Floor(($W - $text.Length) / 2))
    return (Row (' ' * $pad + $text) 0)
}

function Wrap {
    param([string]$text, [int]$width)
    $words = @($text -split '\s+' | Where-Object { $_ -ne '' })
    $lines = @()
    $cur = ''
    foreach ($word in $words) {
        $candidate = if ($cur) { "$cur $word" } else { $word }
        if ($candidate.Length -le $width) {
            $cur = $candidate
        } else {
            if ($cur) { $lines += $cur }
            $cur = $word
        }
    }
    if ($cur) { $lines += $cur }
    if ($lines.Count -eq 0) { $lines = @('') }
    return ,$lines
}

# ASCII-баннер «QUIZ» (figlet standard).
$BANNER = @(
    '  ___  _   _ ___ _____',
    ' / _ \| | | |_ _|__  /',
    '| | | | | | || |  / /',
    '| |_| | |_| || | / /_',
    ' \__\_\\___/|___/____|'
)

function Print-Banner {
    $blockW = ($BANNER | Measure-Object -Property Length -Maximum).Maximum
    $left = [Math]::Max(0, [int][Math]::Floor(($W - $blockW) / 2))
    foreach ($line in $BANNER) {
        Write-Host (Row ((' ' * $left) + $line) 0) -ForegroundColor Green
    }
}

# ── Помощники по лесенке ─────────────────────────────────────────────────
function Prize-ForLevel([int]$level) {
    if ($level -le 0) { return 'ничего' }
    return $PRIZE_LADDER[$level - 1].prize
}

function Guaranteed-Level([int]$level) {
    # Наивысший несгораемый уровень, не превышающий $level (0, если такого нет).
    $g = 0
    foreach ($item in $PRIZE_LADDER) {
        if ($item.level -le $level -and $item.checkpoint) { $g = $item.level }
    }
    return $g
}

function Bonus-Text([bool]$won, [int]$levelReached) {
    if ($won) { return $PRIZE_15_TEXT }
    $g = Guaranteed-Level $levelReached
    if ($g -ge 10) { return $PRIZE_10_TEXT }
    if ($g -ge 5)  { return $PRIZE_5_TEXT }
    return $null
}

# ── Подсказки ────────────────────────────────────────────────────────────
function Lifeline-FiftyFifty($question) {
    # Скрыть два неверных варианта: оставить правильный и один случайный неверный.
    $correct = $question.correct
    $wrong   = $LETTERS | Where-Object { $_ -ne $correct }
    $keep    = $wrong | Get-Random
    return @($wrong | Where-Object { $_ -ne $keep })
}

function Lifeline-Audience($question, $hidden) {
    # Голоса зала с перекосом к правильному ответу.
    $avail   = $LETTERS | Where-Object { $_ -notin $hidden }
    $correct = $question.correct
    $share   = Get-Random -Minimum 45 -Maximum 71   # 45..70
    $votes   = @{ $correct = $share }
    $rest    = @($avail | Where-Object { $_ -ne $correct })
    $remaining = 100 - $share
    for ($i = 0; $i -lt $rest.Count; $i++) {
        if ($i -eq $rest.Count - 1) {
            $votes[$rest[$i]] = $remaining
        } else {
            $v = Get-Random -Minimum 0 -Maximum ($remaining + 1)
            $votes[$rest[$i]] = $v
            $remaining -= $v
        }
    }
    return $votes
}

function Lifeline-Friend { return ($FRIEND_ANSWERS | Get-Random) }

# ── Отрисовка ────────────────────────────────────────────────────────────
function Available-Letters($hidden) {
    return @($LETTERS | Where-Object { $_ -notin $hidden })
}

function Show-Intro {
    Clear-Host
    Write-Host ''
    Write-Host (Hr '=') -ForegroundColor Green
    Print-Banner
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row-Center 'КТО ХОЧЕТ СТАТЬ МИЛЛИОНЕРОМ') -ForegroundColor White
    Write-Host (Row-Center '~ По мотивам «Званого ужина» (РЕН ТВ) ~') -ForegroundColor DarkGray
    Write-Host (Hr '-') -ForegroundColor Green
    $body = 'Каждая игра — случайный вечер недели с одним из героев «Званого ' +
            'ужина». Перед тобой денежная лесенка из 15 вопросов: от 100 рублей ' +
            'до миллиона. Один неверный ответ завершает игру, но 1 000 руб (ур. 5) ' +
            'и 32 000 руб (ур. 10) — несгораемые [*]. В запасе три подсказки: ' +
            '50:50, помощь зала и звонок другу.'
    foreach ($line in (Wrap $body ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor Gray
    }
    Write-Host (Row '')
    Write-Host (Row 'Готов(а) сесть за стол?') -ForegroundColor White
    Write-Host (Hr '=') -ForegroundColor Green
    Read-Host '   Нажми Enter, чтобы начать игру' | Out-Null
}

function Render-Question($game, $level, $hidden) {
    Clear-Host
    $info = $DAYS[$game.day]
    $guaranteed = Guaranteed-Level ($level - 1)
    $guaranteedTxt = if ($guaranteed -gt 0) { Prize-ForLevel $guaranteed } else { '—' }
    $q = $game.questions[$level - 1]

    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row "Вопрос $level из $QUESTIONS_PER_GAME") -ForegroundColor White
    foreach ($line in (Wrap "Вечер: $($info.host) ($($info.weekday))" ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor DarkGray
    }
    foreach ($line in (Wrap "Играем за:   $(Prize-ForLevel $level)" ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor Yellow
    }
    foreach ($line in (Wrap "Несгораемое: $guaranteedTxt" ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor Cyan
    }
    Write-Host (Hr '-') -ForegroundColor Green
    foreach ($line in (Wrap $q.question ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor White
    }
    Write-Host (Row '')
    foreach ($letter in (Available-Letters $hidden)) {
        $optLines = @(Wrap ("$letter) " + $q.options.$letter) ($W - 6))
        for ($i = 0; $i -lt $optLines.Count; $i++) {
            $prefix = if ($i -eq 0) { ' ' } else { '   ' }
            Write-Host (Row ($prefix + $optLines[$i])) -ForegroundColor Gray
        }
    }
    Write-Host (Hr '=') -ForegroundColor Green

    $ll = @()
    if (-not $game.fifty)    { $ll += '1=50:50' }
    if (-not $game.audience) { $ll += '2=зал' }
    if (-not $game.friend)   { $ll += '3=друг' }
    $ll += 'L=лесенка'
    $ll += 'Q=выход'
    Write-Host ('   Команды: ' + ($ll -join '   ')) -ForegroundColor DarkGray
}

function Render-Ladder([int]$current) {
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row-Center 'ПРИЗОВАЯ ЛЕСЕНКА') -ForegroundColor White
    Write-Host (Hr '-') -ForegroundColor Green
    $limit = $W - 2
    for ($i = $PRIZE_LADDER.Count - 1; $i -ge 0; $i--) {
        $item = $PRIZE_LADDER[$i]
        $lvl  = $item.level
        $marker = if ($lvl -eq $current) { '>>' } else { '  ' }
        $lock   = if ($item.checkpoint) { '[*]' } else { '   ' }
        $text = '{0} {1,2}. {2} {3}' -f $marker, $lvl, $lock, $item.prize
        if ($text.Length -gt $limit) { $text = $text.Substring(0, $limit - 2) + '..' }
        if ($lvl -eq $current) {
            Write-Host (Row $text) -ForegroundColor Yellow
        } elseif ($item.checkpoint) {
            Write-Host (Row $text) -ForegroundColor Cyan
        } else {
            Write-Host (Row $text) -ForegroundColor DarkGreen
        }
    }
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host '   [*] — несгораемый уровень. >> — текущий вопрос.' -ForegroundColor DarkGray
}

function Show-Audience($votes, $hidden) {
    $barLen = 24
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row 'ПОМОЩЬ ЗАЛА') -ForegroundColor Magenta
    Write-Host (Hr '-') -ForegroundColor Green
    foreach ($letter in (Available-Letters $hidden)) {
        $pct    = [int]$votes[$letter]
        $filled = [int][Math]::Round($pct / 100 * $barLen)
        $bar    = ('#' * $filled) + ('-' * ($barLen - $filled))
        Write-Host (Row ("{0} |{1}| {2,3}%" -f $letter, $bar, $pct)) -ForegroundColor Magenta
    }
    Write-Host (Hr '=') -ForegroundColor Green
}

function Show-Friend {
    param([string]$text)
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row 'ЗВОНОК ДРУГУ  *звонит телефон*') -ForegroundColor Magenta
    Write-Host (Hr '-') -ForegroundColor Green
    foreach ($line in (Wrap ("— $text") ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor Cyan
    }
    Write-Host (Hr '=') -ForegroundColor Green
}

# Призовой текст печатаем БЕЗ боковых рамок, чтобы длинные ссылки
# не обрезались по ширине холста и оставались кликабельными.
function Print-Bonus {
    param([string]$text)
    Write-Host ''
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row-Center 'ВАШ ПРИЗ') -ForegroundColor Yellow
    Write-Host (Hr '=') -ForegroundColor Green
    foreach ($para in ($text -split '\r?\n')) {
        if ($para.Trim() -eq '') { Write-Host ''; continue }
        if ($para -notmatch '\s') {
            Write-Host ('   ' + $para) -ForegroundColor Cyan        # цельная ссылка
        } else {
            foreach ($line in (Wrap $para ($W - 4))) {
                Write-Host ('   ' + $line) -ForegroundColor Cyan
            }
        }
    }
    Write-Host ''
}

# ── Загрузка вопросов и сборка игры (с «хакерской» инициализацией) ─────────
function New-Game {
    Clear-Host
    Write-Host ''
    Write-Host (Hr '=') -ForegroundColor Green
    Write-Host (Row-Center '[ ПОДКЛЮЧЕНИЕ К СЕРВЕРУ ]') -ForegroundColor Green
    Write-Host (Hr '=') -ForegroundColor Green
    foreach ($step in @(
        '> init secure channel ............. ok',
        '> TLS 1.2 handshake ............... ok',
        '> fetch data/questions.json ...... ...')) {
        Write-Host (Row $step) -ForegroundColor DarkGreen
        Start-Sleep -Milliseconds 200
    }

    try {
        $all = Invoke-RestMethod -Uri $QUESTIONS_URL -UseBasicParsing
    } catch {
        Write-Host (Row '> ACCESS DENIED — нет соединения') -ForegroundColor Red
        Write-Host (Row "  $($_.Exception.Message)") -ForegroundColor DarkGray
        Write-Host (Hr '=') -ForegroundColor Red
        exit 1
    }

    Write-Host (Row '> ACCESS GRANTED .................. ok') -ForegroundColor Green
    Write-Host (Hr '=') -ForegroundColor Green
    Start-Sleep -Milliseconds 400

    $days = @($all | Select-Object -ExpandProperty day -Unique | Sort-Object)
    $day  = $days | Get-Random
    $sets = @($all | Where-Object { $_.day -eq $day } |
                     Select-Object -ExpandProperty set -Unique | Sort-Object)

    $questions = foreach ($s in $sets) {
        @($all | Where-Object { $_.day -eq $day -and $_.set -eq $s }) | Get-Random
    }
    $questions = @($questions | Select-Object -First $QUESTIONS_PER_GAME)

    return [pscustomobject]@{
        day       = $day
        questions = $questions
        fifty     = $false
        audience  = $false
        friend    = $false
    }
}

# ── Главный цикл ─────────────────────────────────────────────────────────
function Play-Game {
    $game = New-Game
    $total = [Math]::Min($QUESTIONS_PER_GAME, $game.questions.Count)

    for ($level = 1; $level -le $total; $level++) {
        $q = $game.questions[$level - 1]
        $hidden = @()
        Render-Question $game $level $hidden

        $chosen = $null
        while (-not $chosen) {
            $inp = (Read-Host '   Твой ход').Trim().ToUpper()
            # Кириллическая раскладка → латиница (А/В/С/Д, Л=лесенка, Й=выход).
            $map = @{ 'А'='A'; 'В'='B'; 'С'='C'; 'Д'='D'; 'Л'='L'; 'Й'='Q' }
            if ($map.ContainsKey($inp)) { $inp = $map[$inp] }

            switch -Regex ($inp) {
                '^(1|50)$' {
                    if ($game.fifty) { Write-Host '   Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.fifty = $true
                    $hidden = Lifeline-FiftyFifty $q
                    Render-Question $game $level $hidden
                    Write-Host '   50:50 — убрали два неверных варианта!' -ForegroundColor Yellow
                    break
                }
                '^2$' {
                    if ($game.audience) { Write-Host '   Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.audience = $true
                    $votes = Lifeline-Audience $q $hidden
                    Render-Question $game $level $hidden
                    Show-Audience $votes $hidden
                    break
                }
                '^3$' {
                    if ($game.friend) { Write-Host '   Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.friend = $true
                    Render-Question $game $level $hidden
                    Show-Friend (Lifeline-Friend)
                    break
                }
                '^L$' {
                    Render-Question $game $level $hidden
                    Render-Ladder $level
                    break
                }
                '^Q$' {
                    Write-Host ''
                    Write-Host '   Игра прервана. Возвращайся за стол!' -ForegroundColor DarkGray
                    return
                }
                '^[ABCD]$' {
                    if ($inp -in (Available-Letters $hidden)) {
                        $chosen = $inp
                    } else {
                        Write-Host '   Этот вариант скрыт. Выбери из доступных.' -ForegroundColor DarkGray
                    }
                    break
                }
                default {
                    Write-Host '   Не понял. A/B/C/D, цифра подсказки, L или Q.' -ForegroundColor DarkGray
                }
            }
        }

        # Обработка ответа
        if ($chosen -eq $q.correct) {
            Write-Host ''
            Write-Host (Hr '=') -ForegroundColor Green
            Write-Host (Row "ВЕРНО! $chosen) $($q.options.$chosen)") -ForegroundColor Green
            Write-Host (Row "Забрано: $(Prize-ForLevel $level)") -ForegroundColor Green
            Write-Host (Hr '=') -ForegroundColor Green
            if ($level -lt $total) {
                Read-Host '   Enter — следующий вопрос' | Out-Null
            }
        } else {
            Show-GameOver $false ($level - 1) $chosen $q
            return
        }
    }

    # Прошёл все 15 — победа.
    Show-GameOver $true $total $null $null
}

function Show-GameOver {
    param([bool]$won, [int]$reached, $chosen, $q)
    Clear-Host
    if ($won) {
        Write-Host (Hr '=') -ForegroundColor Green
        Write-Host (Row-Center '$$$   ПОБЕДА!   $$$') -ForegroundColor Green
        Write-Host (Row '')
        Write-Host (Row-Center 'Ты ответил на все 15 вопросов!') -ForegroundColor White
        Write-Host (Hr '-') -ForegroundColor Green
        foreach ($line in (Wrap "ГЛАВНЫЙ ПРИЗ: $(Prize-ForLevel 15)" ($W - 4))) {
            Write-Host (Row $line) -ForegroundColor Yellow
        }
        Write-Host (Row '')
        Write-Host (Row 'Зал аплодирует стоя!  \o/') -ForegroundColor White
        Write-Host (Hr '=') -ForegroundColor Green
        $bonus = Bonus-Text $true $reached
        if ($bonus) { Print-Bonus $bonus }
        return
    }

    Write-Host (Hr '=') -ForegroundColor Red
    Write-Host (Row-Center 'ИГРА ОКОНЧЕНА') -ForegroundColor Red
    Write-Host (Hr '-') -ForegroundColor Red
    foreach ($line in (Wrap "Увы, неверно. Ты выбрал: $chosen" ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor Red
    }
    $ct = $q.options.$($q.correct)
    foreach ($line in (Wrap "Правильный ответ: $($q.correct)) $ct" ($W - 4))) {
        Write-Host (Row $line) -ForegroundColor White
    }
    if ($reached -le 0) {
        foreach ($line in (Wrap 'Ты не взял ни одного уровня — но это только начало!' ($W - 4))) {
            Write-Host (Row $line) -ForegroundColor White
        }
    } else {
        foreach ($line in (Wrap "Ты дошёл до уровня $reached из 15." ($W - 4))) {
            Write-Host (Row $line) -ForegroundColor White
        }
        foreach ($line in (Wrap "Забираешь: $(Prize-ForLevel $reached)" ($W - 4))) {
            Write-Host (Row $line) -ForegroundColor Yellow
        }
    }
    Write-Host (Hr '=') -ForegroundColor Red
    $bonus = Bonus-Text $false $reached
    if ($bonus) { Print-Bonus $bonus }
}

# ── Точка входа ──────────────────────────────────────────────────────────
try { $Host.UI.RawUI.WindowTitle = 'Званый ужин — викторина' } catch {}

Show-Intro

while ($true) {
    Play-Game
    Write-Host ''
    $again = (Read-Host '   Сыграть ещё? (Y/N)').Trim().ToUpper()
    if ($again -ne 'Y' -and $again -ne 'Д') { break }
}

Write-Host ''
Write-Host (Hr '=') -ForegroundColor Green
Write-Host (Row-Center 'Спасибо за игру! Заходите на «Званый ужин» ещё.') -ForegroundColor Cyan
Write-Host (Hr '=') -ForegroundColor Green
Write-Host ''
