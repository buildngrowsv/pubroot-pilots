#!/usr/bin/env bash
# Runs every case through 8 negotiators in-process (no network). Deterministic; no keys or accounts.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
mkdir -p results
node js/run_node.js < cases.json > results/node.json
"$PY" py/run_py.py < cases.json > results/py.json
(cd go && go build -o ../.bin-go-accept .)
./.bin-go-accept < cases.json > results/go.json
python3 analyze.py > results/report.txt; head -12 results/report.txt
{
  echo "node $(node -v)"
  for p in accepts accepts1 negotiator accepts1/node_modules/negotiator; do echo "$p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  "$PY" -c "import sys, importlib.metadata as m; print('python', sys.version.split()[0]); [print(p, m.version(p)) for p in ('werkzeug','django','falcon')]"
  go version
  grep -E "goautoneg|gddo|contenttype" go/go.mod | sed 's/^\s*//'
} > results/versions.txt
