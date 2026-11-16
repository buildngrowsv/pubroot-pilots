#!/usr/bin/env python3
"""rw_cases.json from the committed snapshot realworld/gha_cron.json (GitHub Actions schedule expressions)."""
import json, sys
sys.path.insert(0, "."); import gen_cases as g
d = json.load(open("realworld/gha_cron.json")); out = []
for i, (e, n) in enumerate(d["expressions"].items()):
    try: exp = g.reading(e)
    except g.Invalid: exp = "INVALID"
    except g.Open: exp = "OPEN"
    out.append(dict(id=f"RW{i + 1:03d}", group="realworld", expr=e, expect=exp, files=n))
json.dump(dict(start=g.START, n=g.N, cases=out), open("rw_cases.json", "w"), indent=1)
print(len(out), "expressions")
