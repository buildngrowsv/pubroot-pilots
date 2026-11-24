#!/usr/bin/env bash
# Builds the Go and Rust runners, runs every splitter and quoter on the case lists, runs the POSIX sh reference
# (dash, bash --posix) and writes results/. Local only; no network after installation. Cost: $0.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
mkdir -p results
(cd go && go build -o ../.bin-go-words .)
(cd rs && cargo build --release --locked -q)
for m in split quote; do
  [ $m = split ] && IN=cases.json || IN=quote_cases.json
  "$PY" py/run.py $m $IN > results/.py.$m.json
  node js/run.mjs $m $IN > results/.js.$m.json
  ./.bin-go-words $m $IN > results/.go.$m.json
  ./rs/target/release/rs-words $m $IN > results/.rs.$m.json
  python3 - "$m" <<'PY'
import json, sys
m = sys.argv[1]; out = {}
for l in ("py", "js", "go", "rs"): out.update(json.load(open(f"results/.{l}.{m}.json")))
json.dump(dict(sorted(out.items())), open(f"results/{m}.json", "w"), indent=1, ensure_ascii=False)
PY
  rm -f results/.*.$m.json
done
python3 oracle.py split cases.json > results/sh_split.json
python3 oracle.py quote quote_cases.json results/quote.json > results/sh_quote.json
python3 analyze.py > results/report.txt; head -22 results/report.txt
python3 realworld/analyze_rw.py "$PY" > results/realworld.txt; cat results/realworld.txt
{
  echo "dash $(dpkg-query -W -f='${Version}' dash 2>/dev/null)"; echo "$(bash --version | head -1)"
  echo "python $("$PY" -c 'import sys; print(sys.version.split()[0])') (shlex from the standard library)"
  echo "node $(node -v)"
  for p in shell-quote string-argv shlex shell-escape; do echo "npm $p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  go version; awk '/^\t/{print "go", $1, $2}' go/go.mod
  rustc --version; for c in shlex shell-words; do awk -v n="$c" '$0=="name = \""n"\""{getline; print "crate", n, $3}' rs/Cargo.lock | tr -d '"'; done
} > results/versions.txt
