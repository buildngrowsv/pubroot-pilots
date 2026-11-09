#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
mkdir -p "$HERE/results"
python3 "$HERE/gen_cases.py"
node "$HERE/js/run_express.mjs" < "$HERE/cases.json" > "$HERE/results/express.json"
"$PY" "$HERE/py/run_py.py" < "$HERE/cases.json" > "$HERE/results/py.json"
"$PY" "$HERE/analyze.py"
{
  echo "express-cors $(node -e "console.log(require('$HERE/js/node_modules/cors/package.json').version)")"
  echo "express $(node -e "console.log(require('$HERE/js/node_modules/express/package.json').version)")"
  echo "node $(node -v)"
  "$PY" -c "import flask,flask_cors,starlette; print(f'flask {flask.__version__}'); print(f'flask-cors {flask_cors.__version__}'); print(f'starlette {starlette.__version__}')"
} > "$HERE/results/versions.txt"
