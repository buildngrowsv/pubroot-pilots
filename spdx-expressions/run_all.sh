#!/usr/bin/env bash
# Runs every case through 6 SPDX expression implementations in-process (no network, no keys or accounts).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-.venv/bin/python}
python3 gen_cases.py >/dev/null
mkdir -p results
node js/run_node.js < cases.json > results/node.json
"$PY" py/run_py.py < cases.json > results/py.json
(cd go && go build -o ../.bin-go-spdx .) && ./.bin-go-spdx < cases.json > results/go.json
(cd rs && cargo build --release --locked -q) && ./rs/target/release/spdx_pilot < cases.json > results/rs.json
# real-world sample: committed snapshot realworld/strings.json (fetched once by realworld/fetch.py)
python3 realworld/gen_rw.py >/dev/null
node js/run_node.js < rw_cases.json > results/rw_node.json
"$PY" py/run_py.py < rw_cases.json > results/rw_py.json
./.bin-go-spdx < rw_cases.json > results/rw_go.json
./rs/target/release/spdx_pilot < rw_cases.json > results/rw_rs.json
python3 analyze.py > results/report.txt; head -20 results/report.txt
{
  echo "node $(node -v)"
  for p in spdx-expression-parse sep3 spdx-satisfies spdx-license-ids spdx-exceptions; do echo "$p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  "$PY" -c "import sys, importlib.metadata as m; print('python', sys.version.split()[0]); [print(p, m.version(p)) for p in ('license-expression','packaging','boolean.py')]"
  go version; grep go-spdx go/go.mod | sed 's/^\s*//'
  rustc --version; grep -A1 'name = "spdx"' rs/Cargo.lock | tr '\n' ' '; echo
  echo "go-spdx license list $(python3 -c "import json;print(json.load(open('results/go.json'))['_list_version'])")"
  echo "packaging license list $("$PY" -c "from packaging.licenses import _spdx; print(_spdx.VERSION)")"
  echo "spdx-rs license list $(python3 -c "import json;print(json.load(open('results/rs.json'))['_list_version'])")"
} > results/versions.txt
