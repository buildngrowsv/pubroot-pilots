#!/usr/bin/env bash
# Pins data/d.txt's mtime, starts the local servers (127.0.0.1 only, each in its own session), drives every case
# through each, and stops ONLY the servers this script started.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
touch -d "2026-01-15T12:00:00Z" data/d.txt
mkdir -p results
(cd go && go build -o ../.bin-go-cond .)
(cd rs && cargo build --release --locked -q)
declare -A CMD=(
  [express]="node js/express_server.mjs 18201"
  [fastify_send]="node js/fastify_send_server.mjs 18202"
  [sirv]="node js/sirv_server.mjs 18203"
  [serve_handler]="node js/serve_handler_server.mjs 18204"
  [starlette]="$PY -m uvicorn py.starlette_app:app --host 127.0.0.1 --port 18205 --log-level warning"
  [aiohttp]="$PY py/aiohttp_server.py 18206"
  [werkzeug]="$PY py/werkzeug_server.py 18207"
  [tornado]="$PY py/tornado_server.py 18208"
  [falcon]="$PY -m uvicorn py.falcon_app:app --host 127.0.0.1 --port 18209 --log-level warning"
  [django]="$PY py/django_server.py 18210"
  [go_servecontent]="./.bin-go-cond servecontent 18211"
  [go_fileserver]="./.bin-go-cond fileserver 18212"
  [tower_http]="./rs/target/release/tower_servedir 18213"
  [actix_files]="./rs/target/release/actix_files 18214"
)
ORDER=(express fastify_send sirv serve_handler starlette aiohttp werkzeug tornado falcon django go_servecontent go_fileserver tower_http actix_files)
declare -A PORT; i=18201; for n in "${ORDER[@]}"; do PORT[$n]=$i; i=$((i+1)); done
PIDS=()
cleanup() { for p in "${PIDS[@]}"; do kill -- "-$p" 2>/dev/null || true; done; }
trap cleanup EXIT
for n in "${ORDER[@]}"; do setsid ${CMD[$n]} >/dev/null 2>&1 & PIDS+=($!); done
for n in "${ORDER[@]}"; do
  for i in $(seq 1 100); do (exec 3<>/dev/tcp/127.0.0.1/${PORT[$n]}) 2>/dev/null && break; sleep 0.2; done
done
for n in "${ORDER[@]}"; do python3 driver.py "$n" "${PORT[$n]}" > "results/$n.json"; done
python3 analyze.py > results/report.txt; head -30 results/report.txt
{
  echo "node $(node -v)"
  for p in express send etag fresh @fastify/send sirv serve-handler; do echo "$p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  "$PY" -c "import sys, importlib.metadata as m; print('python', sys.version.split()[0]); [print(p, m.version(p)) for p in ('starlette','uvicorn','h11','aiohttp','werkzeug','tornado','falcon','django')]"
  go version
  rustc --version
  for c in axum tower-http actix-web actix-files; do awk -v n="$c" '$0=="name = \""n"\""{getline; print n, $3}' rs/Cargo.lock | tr -d '"'; done
} > results/versions.txt
