#!/usr/bin/env bash
# Extra stability check: N fresh case sets (default 10) through CPython, Node and Bun (workerd is covered by run_all.sh),
# then list any (runtime, subject, case) whose verdict changed between case sets. Also runs py/nopad_sweep.py.
set -euo pipefail
cd "$(dirname "$0")"; PY="${PY:-python3}"; N="${N:-10}"; d=results/stability; mkdir -p "$d"
for i in $(seq 1 "$N"); do
  python3 gen_cases.py "$d/c$i.json" >/dev/null
  "$PY" py/run_py.py "$d/c$i.json" "$d/py$i.jsonl" >/dev/null
  node js/run_node.mjs "$d/c$i.json" "$d/node$i.jsonl" >/dev/null
  bun js/run_node.mjs "$d/c$i.json" "$d/bun$i.jsonl" >/dev/null 2>&1
  sleep 1
done
python3 - "$d" "$N" <<'PY' | tee results/stability.txt
import json, sys, collections
d, n = sys.argv[1], int(sys.argv[2]); var = collections.defaultdict(collections.Counter)
for i in range(1, n + 1):
    for rt in ("py", "node", "bun"):
        for r in map(json.loads, open(f"{d}/{rt}{i}.jsonl")): var[(r["runtime"], r["subject"], r["case"])][r["verdict"]] += 1
unstable = {k: dict(v) for k, v in var.items() if len(v) > 1}
print(f"case sets: {n}; (runtime, subject, case) triples: {len(var)}; with more than one verdict: {len(unstable)}")
for k, v in sorted(unstable.items()): print(" | ".join(k), v)
PY
"$PY" py/nopad_sweep.py | tee results/nopad_sweep.txt
