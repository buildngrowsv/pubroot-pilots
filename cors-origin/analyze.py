#!/usr/bin/env python3
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
cases = json.load(open(os.path.join(HERE, "cases.json")))
express = {r["id"]: r for r in json.load(open(os.path.join(HERE, "results", "express.json")))}
py = json.load(open(os.path.join(HERE, "results", "py.json")))
star = {r["id"]: r for r in py["starlette"]}
flask = {r["id"]: r for r in py["flask_cors"]}

def norm(v):
    if v is None: return None
    return str(v)

rows = []
disagree = 0
for c in cases:
    i = c["id"]
    a = norm(express[i].get("acao"))
    b = norm(star[i].get("acao"))
    d = norm(flask[i].get("acao"))
    same = (a == b == d)
    if not same:
        disagree += 1
    rows.append({"id": i, "origin": c["origin"], "express": a, "starlette": b, "flask_cors": d, "agree": same})

summary = {"n_cases": len(cases), "cases_disagree_any": disagree, "rows": rows}
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=2)
print(f"cases={len(cases)} disagree_any={disagree}")
for r in rows:
    if not r["agree"]:
        print(f"  {r['id']}: express={r['express']} starlette={r['starlette']} flask={r['flask_cors']}")
