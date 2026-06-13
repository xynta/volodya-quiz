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

function Render-Question($game, $level, $hidden) {
    Clear-Host
    $info = $DAYS[$game.day]
    $guaranteed = Guaranteed-Level ($level - 1)
    $guaranteedTxt = if ($guaranteed -gt 0) { Prize-ForLevel $guaranteed } else { '—' }
    $q = $game.questions[$level - 1]

    Write-Host ''
    Write-Host '  ════════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
    Write-Host "  ЗВАНЫЙ УЖИН — $($info.weekday), у $($info.host)" -ForegroundColor Cyan
    Write-Host '  ════════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
    Write-Host ''
    Write-Host "  Вопрос $level из $QUESTIONS_PER_GAME" -ForegroundColor White
    Write-Host "  Играем за:    $(Prize-ForLevel $level)" -ForegroundColor Yellow
    Write-Host "  Несгораемое:  $guaranteedTxt" -ForegroundColor DarkYellow
    Write-Host ''
    Write-Host "  $($q.question)" -ForegroundColor White
    Write-Host ''
    foreach ($letter in (Available-Letters $hidden)) {
        Write-Host "    $letter) $($q.options.$letter)" -ForegroundColor Gray
    }
    Write-Host ''
    $ll = @()
    if (-not $game.fifty)    { $ll += '1 = 50:50' }
    if (-not $game.audience) { $ll += '2 = помощь зала' }
    if (-not $game.friend)   { $ll += '3 = звонок другу' }
    if ($ll.Count) {
        Write-Host "  Подсказки:  $($ll -join '   ')   (Q — выход)" -ForegroundColor Magenta
    } else {
        Write-Host '  Подсказки израсходованы.   (Q — выход)' -ForegroundColor DarkGray
    }
    Write-Host ''
}

# ── Загрузка вопросов и сборка игры ──────────────────────────────────────
function New-Game {
    try {
        $all = Invoke-RestMethod -Uri $QUESTIONS_URL -UseBasicParsing
    } catch {
        Write-Host ''
        Write-Host '  Не удалось скачать вопросы. Проверь интернет и попробуй снова.' -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor DarkGray
        exit 1
    }

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
            $inp = (Read-Host '  Твой ответ').Trim().ToUpper()
            switch -Regex ($inp) {
                '^(1|50)$' {
                    if ($game.fifty) { Write-Host '  Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.fifty = $true
                    $hidden = Lifeline-FiftyFifty $q
                    Render-Question $game $level $hidden
                    break
                }
                '^2$' {
                    if ($game.audience) { Write-Host '  Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.audience = $true
                    $votes = Lifeline-Audience $q $hidden
                    Write-Host '  Зал голосует:' -ForegroundColor Magenta
                    foreach ($letter in (Available-Letters $hidden)) {
                        $pct = [int]$votes[$letter]
                        $bar = '#' * [int][Math]::Round($pct / 4)
                        Write-Host ("    {0}  {1,3}%  {2}" -f $letter, $pct, $bar) -ForegroundColor Magenta
                    }
                    Write-Host ''
                    break
                }
                '^3$' {
                    if ($game.friend) { Write-Host '  Уже использовано.' -ForegroundColor DarkGray; break }
                    $game.friend = $true
                    Write-Host "  Друг отвечает: «$(Lifeline-Friend)»" -ForegroundColor Magenta
                    Write-Host ''
                    break
                }
                '^Q$' {
                    Write-Host ''
                    Write-Host '  Игра прервана. Возвращайся за стол!' -ForegroundColor DarkGray
                    return
                }
                '^[ABCD]$' {
                    if ($inp -in (Available-Letters $hidden)) {
                        $chosen = $inp
                    } else {
                        Write-Host '  Этот вариант скрыт. Выбери из доступных.' -ForegroundColor DarkGray
                    }
                    break
                }
                default {
                    Write-Host '  Не понял. Нажми A/B/C/D или цифру подсказки.' -ForegroundColor DarkGray
                }
            }
        }

        # Обработка ответа
        if ($chosen -eq $q.correct) {
            Write-Host ''
            Write-Host "  ВЕРНО! $chosen) $($q.options.$chosen)" -ForegroundColor Green
            Write-Host "  Забрано: $(Prize-ForLevel $level)" -ForegroundColor Green
            if ($level -lt $total) {
                Write-Host ''
                Read-Host '  Enter — следующий вопрос' | Out-Null
            }
        } else {
            Show-GameOver $game $level $false ($level - 1) $chosen $q
            return
        }
    }

    # Прошёл все 15 — победа.
    Show-GameOver $game $total $true $total $null $null
}

function Show-GameOver($game, $levelReached, [bool]$won, [int]$reached, $chosen, $q) {
    Write-Host ''
    Write-Host '  ════════════════════════════════════════════════════════════' -ForegroundColor DarkCyan
    if ($won) {
        Write-Host '  ПОБЕДА! Ты ответил на все 15 вопросов!' -ForegroundColor Green
        Write-Host "  Главный приз: $(Prize-ForLevel 15)" -ForegroundColor Yellow
    } else {
        Write-Host "  Увы, неверно. Ты выбрал $chosen." -ForegroundColor Red
        Write-Host "  Правильный ответ: $($q.correct)) $($q.options.$($q.correct))" -ForegroundColor Yellow
        if ($reached -le 0) {
            Write-Host '  Ты не взял ни одного уровня — но это только начало!' -ForegroundColor White
        } else {
            Write-Host "  Ты дошёл до уровня $reached из 15." -ForegroundColor White
            Write-Host "  Забираешь: $(Prize-ForLevel $reached)" -ForegroundColor Yellow
        }
    }
    Write-Host '  ════════════════════════════════════════════════════════════' -ForegroundColor DarkCyan

    $bonus = Bonus-Text $won $reached
    if ($bonus) {
        Write-Host ''
        Write-Host $bonus -ForegroundColor Cyan
    }
    Write-Host ''
}

# ── Точка входа ──────────────────────────────────────────────────────────
try { $Host.UI.RawUI.WindowTitle = 'Званый ужин — викторина' } catch {}

while ($true) {
    Play-Game
    Write-Host ''
    $again = (Read-Host '  Сыграть ещё? (Y/N)').Trim().ToUpper()
    if ($again -ne 'Y' -and $again -ne 'Д') { break }
}

Write-Host ''
Write-Host '  Спасибо за игру!' -ForegroundColor Cyan
Write-Host ''
