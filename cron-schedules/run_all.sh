#!/usr/bin/env bash
# Runs every case through 9 cron libraries (Python, Node.js, Go) in-process; no network, keys or accounts.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-.venv/bin/python}
python3 gen_cases.py >/dev/null
mkdir -p results
"$PY" py/run_py.py < cases.json > results/py.json
node js/run_node.js < cases.json > results/node.json
(cd go && go build -o ../.bin-go-cron .) && ./.bin-go-cron < cases.json > results/go.json
python3 realworld/gen_rw.py >/dev/null
"$PY" py/run_py.py < rw_cases.json > results/rw_py.json
node js/run_node.js < rw_cases.json > results/rw_node.json
./.bin-go-cron < rw_cases.json > results/rw_go.json
python3 analyze.py > results/report.txt; head -16 results/report.txt
{
  echo "node $(node -v)"
  for p in cron-parser croner cron luxon; do echo "$p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  "$PY" -c "import sys, importlib.metadata as m; print('python', sys.version.split()[0]); [print(p, m.version(p)) for p in ('croniter','cronsim','APScheduler','python-dateutil','tzlocal')]"
  go version; grep -E "robfig|gronx|cronexpr" go/go.mod | sed 's/^\s*//'
} > results/versions.txt
