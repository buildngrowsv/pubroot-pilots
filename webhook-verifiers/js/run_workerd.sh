#!/usr/bin/env bash
# Run the JS subjects inside workerd via `wrangler dev` (local only) on a private port; stops only its own process group.
set -euo pipefail
cd "$(dirname "$0")"; CASES="$1"; OUT="$2"; PORT="${PORT:-18787}"
WRANGLER_SEND_METRICS=false CI=1 setsid npx wrangler dev --port "$PORT" --ip 127.0.0.1 > ../results/wrangler-dev.log 2>&1 &
PGID=$!
trap 'kill -- -$PGID 2>/dev/null || true' EXIT
for i in $(seq 1 60); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" -X POST -d '{"cases":[]}' && break; sleep 1; done
curl -s -X POST --data-binary @"$CASES" "http://127.0.0.1:$PORT/" > "$OUT"
WV=$(grep -o 'workerd [0-9.]*\|wrangler [0-9.]*' ../results/wrangler-dev.log | head -1 || true)
sed -i "s/\"workerd (Miniflare )\"/\"workerd via wrangler $(npx wrangler --version 2>/dev/null | tail -1) dev\"/" "$OUT"
echo "rows: $(wc -l < "$OUT")"
