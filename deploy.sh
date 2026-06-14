#!/usr/bin/env bash
# Деплой бота на сервере (ORACLE2): подтянуть свежий код из origin/main и
# перезапустить systemd-сервис. Папка на сервере — git-checkout (см. README).
#
#   Запуск на сервере:        ./deploy.sh
#   Удалённо одной командой:   ssh ORACLE2 'cd /home/ubuntu/volodya_quiz && ./deploy.sh'
set -euo pipefail

cd "$(dirname "$0")"
UNIT=volodya-quiz-bot

echo "→ git pull (origin/main)"
git pull --ff-only

echo "→ перезапуск $UNIT"
sudo systemctl restart "$UNIT"

# Дать боту подняться и убедиться, что поллинг стартовал.
sleep 6
echo "→ статус: $(systemctl is-active "$UNIT")"
if journalctl -u "$UNIT" -n 20 --no-pager --since "1 minute ago" | grep -q "Run polling"; then
  echo "✓ поллинг запущен · $(git log --oneline -1)"
else
  echo "⚠ нет 'Run polling' в логах — проверь: journalctl -u $UNIT -n 40"
  exit 1
fi
