#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! docker compose -f docker-compose.dev.yml ps --status running --quiet api >/dev/null 2>&1; then
  echo "Stack chưa chạy. Khởi động: docker compose -f docker-compose.dev.yml up -d"
  exit 1
fi
docker compose -f docker-compose.dev.yml exec -T api alembic downgrade base
docker compose -f docker-compose.dev.yml exec -T api alembic upgrade head
echo "Database reset xong."
