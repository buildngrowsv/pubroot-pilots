#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python3}
mkdir -p "$HERE/results"
python3 "$HERE/gen_pages.py"
"$PY" "$HERE/py/run_extract.py"
(cd "$HERE/js" && node run_metascraper.cjs)
"$PY" "$HERE/analyze.py"
{
  echo "extruct $($PY -c 'from importlib.metadata import version; print(version("extruct"))')"
  echo "metascraper $(node -e "console.log(require('./js/node_modules/metascraper/package.json').version)")"
  echo "metascraper-citation $(node -e "console.log(require('./js/node_modules/metascraper-citation/package.json').version)")"
  echo "metascraper-title $(node -e "console.log(require('./js/node_modules/metascraper-title/package.json').version)")"
  echo "node $(node -v)"
  echo "python $($PY -V | awk '{print $2}')"
} > "$HERE/results/versions.txt"
