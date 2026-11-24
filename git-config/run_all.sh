#!/usr/bin/env bash
# Builds the Go and Rust readers, reads every case with git (the reference) and with each library, classes the results
# and writes results/. No network. Cost: $0.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY=${PY:-python3}
python3 gen_cases.py >/dev/null
mkdir -p results
(cd go && go build -o ../.bin-go-gc .)
(cd rs && cargo build --release --locked -q)
"$PY" py/run.py cases.json > results/.py.json
node js/run.mjs cases.json > results/.js.json
./.bin-go-gc cases.json > results/.go.json
./rs/target/release/rs-gitconfig cases.json > results/.rs.json
python3 - <<'PY'
import json
out = {}
for l in ("py", "js", "go", "rs"): out.update(json.load(open(f"results/.{l}.json")))
json.dump(out, open("results/libs.json", "w"), indent=1, ensure_ascii=False)
PY
rm -f results/.py.json results/.js.json results/.go.json results/.rs.json
python3 oracle.py cases.json > results/git.json
python3 analyze.py > results/report.txt; head -14 results/report.txt
if [ -f realworld/snapshot.local.json ]; then python3 realworld/analyze_rw.py "$PY" > results/realworld.txt; cat results/realworld.txt
else echo "realworld/snapshot.local.json missing: run python3 realworld/fetch_gitconfigs.py --restore (network) to include the sample" >&2; fi
{
  git --version
  echo "python $("$PY" -c 'import sys; print(sys.version.split()[0])')"
  "$PY" -c 'import dulwich, git, pygit2; print("dulwich", ".".join(map(str, dulwich.__version__))); print("GitPython", git.__version__); print("pygit2", pygit2.__version__, "libgit2", pygit2.LIBGIT2_VERSION)'
  echo "node $(node -v)"
  for p in parse-git-config ini isomorphic-git; do echo "npm $p $(node -e "console.log(require('./js/node_modules/$p/package.json').version)")"; done
  go version; grep -oE 'github.com/go-git/go-git/v5 v[0-9.]+' go/go.mod | sed 's/^/go /'
  rustc --version; awk '$0=="name = \"gix-config\""{getline; print "crate gix-config", $3}' rs/Cargo.lock | tr -d '"'
} > results/versions.txt
