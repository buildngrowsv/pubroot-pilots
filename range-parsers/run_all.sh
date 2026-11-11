#!/usr/bin/env bash
# Starts six local servers (127.0.0.1 only), drives all cases through each, stops ONLY the servers this script started.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
mkdir -p results
(cd go && go build -o ../.bin-go-range .)
declare -A CMD=(
  [express]="node js/express_server.mjs 18101"
  [fastify_send]="node js/fastify_send_server.mjs 18102"
  [starlette]="$PY -m uvicorn py.starlette_app:app --host 127.0.0.1 --port 18103 --log-level warning"
  [aiohttp]="$PY py/aiohttp_server.py 18104"
  [werkzeug]="$PY py/werkzeug_server.py 18105"
  [tornado]="$PY py/tornado_server.py 18106"
  [go_net_http]="./.bin-go-range 18107"
  [go_godebug_maxranges1]="env GODEBUG=httpservecontentmaxranges=1 ./.bin-go-range 18108"
)
declare -A PORT=([express]=18101 [fastify_send]=18102 [starlette]=18103 [aiohttp]=18104 [werkzeug]=18105 [tornado]=18106 [go_net_http]=18107 [go_godebug_maxranges1]=18108)
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill -- "-$p" 2>/dev/null || true; done; }
trap cleanup EXIT
for n in "${!CMD[@]}"; do setsid ${CMD[$n]} >/dev/null 2>&1 & PIDS+=($!); done
for n in "${!PORT[@]}"; do
  for i in $(seq 1 50); do (exec 3<>/dev/tcp/127.0.0.1/${PORT[$n]}) 2>/dev/null && break; sleep 0.2; done
done
for n in express fastify_send starlette aiohttp werkzeug tornado go_net_http go_godebug_maxranges1; do
  python3 driver.py "$n" "${PORT[$n]}" > "results/$n.json"
done
python3 analyze.py > results/report.txt; head -12 results/report.txt
{
  echo "node $(node -v)"
  for p in express send range-parser @fastify/send; do echo "$p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  "$PY" -c "import sys, importlib.metadata as m; print('python', sys.version.split()[0]); [print(p, m.version(p)) for p in ('starlette','aiohttp','werkzeug','tornado','uvicorn','h11')]"
  go version
} > results/versions.txt
