#!/usr/bin/env python3
"""Python standard library shlex. Usage: run.py split|quote CASES.json > out.json"""
import json, shlex, sys
mode, f = sys.argv[1], sys.argv[2]
def wrap(fn):
    def g(s):
        try: return dict(argv=fn(s))
        except Exception as e: return dict(error=f"{type(e).__name__}: {e}"[:120])
    return g
T = {"shlex (Python)": wrap(shlex.split)} if mode == "split" else {"shlex (Python)": wrap(shlex.quote)}
cases = json.load(open(f))
json.dump({n: {c["id"]: fn(c["s"]) for c in cases} for n, fn in T.items()}, sys.stdout, indent=1, ensure_ascii=False); print()
