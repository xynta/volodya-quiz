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
SINCE="$(date '+%Y-%m-%d %H:%M:%S')"
sudo systemctl restart "$UNIT"

# Бот поднимается ~10-15с (getMe + delete_webhook), поэтому ждём «Run polling»
# в цикле до ~40с, а не фиксированной паузой.
echo -n "→ жду старта поллинга"
for _ in $(seq 1 20); do
  sleep 2; echo -n "."
  if journalctl -u "$UNIT" --no-pager --since "$SINCE" | grep -q "Run polling"; then
    echo " ✓"
    echo "✓ поллинг запущен · статус $(systemctl is-active "$UNIT") · $(git log --oneline -1)"
    exit 0
  fi
done
echo
echo "⚠ за ~40с не увидел 'Run polling'. Статус: $(systemctl is-active "$UNIT")"
echo "  проверь: journalctl -u $UNIT -n 40 --no-pager"
exit 1
