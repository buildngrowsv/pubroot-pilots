#!/usr/bin/env bash
# Full matrix, REPS repetitions. Each repetition regenerates the cases (fresh NOW) and runs CPython, Node, Bun and workerd.
set -euo pipefail
cd "$(dirname "$0")"; PY="${PY:-python3}"; REPS="${REPS:-2}"
for r in $(seq 1 "$REPS"); do
  d="results/rep$r"; mkdir -p "$d"
  python3 gen_cases.py "$d/cases.json"
  "$PY" py/run_py.py "$d/cases.json" "$d/py.jsonl"
  node js/run_node.mjs "$d/cases.json" "$d/node.jsonl"
  bun js/run_node.mjs "$d/cases.json" "$d/bun.jsonl" 2>/dev/null
  js/run_workerd.sh "$PWD/$d/cases.json" "$PWD/$d/workerd.jsonl"
done
python3 analyze.py results
