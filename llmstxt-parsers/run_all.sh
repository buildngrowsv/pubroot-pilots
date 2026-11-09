#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
mkdir -p "$HERE/results"
node "$HERE/js/run_js.cjs"
"$PY" "$HERE/py/run_py.py"
"$PY" "$HERE/analyze.py"
{
  echo "llms-txt $($PY -c 'import llms_txt; print(llms_txt.__version__)')"
  echo "@25xcodes/llmstxt-parser $(node -e "console.log(require('$HERE/js/node_modules/@25xcodes/llmstxt-parser/package.json').version)")"
  echo "parse-llms-txt $(node -e "console.log(require('$HERE/js/node_modules/parse-llms-txt/package.json').version)")"
  echo "node $(node -v)"
} > "$HERE/results/versions.txt"
