#!/usr/bin/env bash
# Builds the Go and Rust parsers, parses every case with distribution/reference (the reference) and each library,
# classes the results and writes results/. No network. Cost: $0.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
mkdir -p results
(cd go && go build -o ../.bin-go-refs .)
(cd rs && cargo build --release --locked -q)
"$PY" py/run.py cases.json > results/.py.json
node js/run.mjs cases.json > results/.js.json
./.bin-go-refs cases.json > results/.go.json
./rs/target/release/rs-refs cases.json > results/.rs.json
python3 - <<'PY'
import json
out = {}
for l in ("go", "py", "js", "rs"): out.update(json.load(open(f"results/.{l}.json")))
json.dump(out, open("results/refs.json", "w"), indent=1, ensure_ascii=False)
PY
rm -f results/.py.json results/.js.json results/.go.json results/.rs.json
python3 analyze.py > results/report.txt; head -12 results/report.txt
python3 realworld/analyze_rw.py "$PY" > results/realworld.txt; cat results/realworld.txt
{
  echo "python $("$PY" -c 'import sys; print(sys.version.split()[0])')"
  "$PY" -m pip list --format=freeze 2>/dev/null | grep -iE '^(docker|docker-image-py)==' | sed 's/^/pypi /'
  echo "node $(node -v)"
  for p in @swimlane/docker-reference docker-parse-image parse-docker-image-name; do echo "npm $p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  go version; grep -oE '(github.com/distribution/reference|github.com/google/go-containerregistry) v[0-9.]+' go/go.mod | sed 's/^/go /'
  rustc --version; awk '$0=="name = \"oci-spec\""{getline; print "crate oci-spec", $3}' rs/Cargo.lock | tr -d '"'
} > results/versions.txt
