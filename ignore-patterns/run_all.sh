#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HERE/results"
python3 "$HERE/gen_cases.py"
python3 "$HERE/run_git.py"
META="$HERE/cases/meta.json"
# Docker via Go patternmatcher
python3 - <<PY
import json, os, subprocess
HERE = "$HERE"
meta_path = os.path.join(HERE, "cases", "meta.json")
meta = json.load(open(meta_path))
out = {}
matcher = os.path.join(HERE, "go", "matcher")
for name in meta["pattern_names"]:
    ign = os.path.join(HERE, "cases", f"{name}.ignore")
    r = subprocess.check_output([matcher, ign, meta_path], text=True)
    out[name] = json.loads(r)
json.dump(out, open(os.path.join(HERE, "results", "moby.json"), "w"), indent=2, sort_keys=True)
print("moby cases", len(out))
PY
# Docker via balena
python3 - <<PY
import json, os, subprocess
HERE = "$HERE"
meta = json.load(open(os.path.join(HERE, "cases", "meta.json")))
out = {}
for name in meta["pattern_names"]:
    ign = os.path.join(HERE, "cases", f"{name}.ignore")
    r = subprocess.check_output(["node", os.path.join(HERE, "js", "run_dockerignore.mjs"), ign, os.path.join(HERE, "cases", "meta.json")], text=True, cwd=os.path.join(HERE, "js"))
    out[name] = json.loads(r)
json.dump(out, open(os.path.join(HERE, "results", "balena.json"), "w"), indent=2, sort_keys=True)
print("balena cases", len(out))
PY
python3 "$HERE/analyze.py"
