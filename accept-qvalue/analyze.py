#!/usr/bin/env python3
import json, os, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
cases = json.load(open(os.path.join(HERE, "cases.json")))
raw = {}
for f in ("node", "py", "go"):
    for k, rows in json.load(open(os.path.join(HERE, "results", f + ".json"))).items(): raw[k] = {r["id"]: r["choice"] for r in rows}
IMPLS = ["accepts2", "accepts1", "werkzeug", "django", "falcon", "goautoneg", "gddo", "contenttype"]
EXP = json.load(open(os.path.join(HERE, "expected.json")))
def show(v): return "none" if v is None else v
rows = []
for c in cases:
    outs = {n: show(raw[n][c["id"]]) for n in IMPLS}
    e = EXP.get(c["id"])
    rows.append({**c, "choices": outs, "n_distinct": len(set(outs.values())), "rfc_reading": e,
                 "matches_reading": {n: (e is not None and outs[n] in e["ok"]) for n in IMPLS}})
pair = {f"{a}~{b}": sum(r["choices"][a] != r["choices"][b] for r in rows) for a, b in itertools.combinations(IMPLS, 2)}
viol = {n: [r["id"] for r in rows if r["rfc_reading"] and r["choices"][n] in r["rfc_reading"]["refused"]] for n in IMPLS}
per = {n: sum(r["matches_reading"][n] for r in rows if r["rfc_reading"]) for n in IMPLS}
summary = {"n_cases": len(rows), "n_impls": len(IMPLS), "cases_disagree_any": sum(r["n_distinct"] > 1 for r in rows),
           "max_distinct": max(r["n_distinct"] for r in rows), "n_cases_with_reading": sum(1 for r in rows if r["rfc_reading"]),
           "matches_reading": per, "refusal_violations": viol, "pairwise_disagreements": pair, "rows": rows}
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1, sort_keys=True)
print(f"cases={len(rows)} disagree_any={summary['cases_disagree_any']} max_distinct={summary['max_distinct']} with_reading={summary['n_cases_with_reading']}")
print("matches RFC 9110 reading:", per)
print("returned a q=0-refused type:", {n: v for n, v in viol.items() if v})
for r in rows:
    print(f"{r['id']} {str(r['accept'])[:44]!r:46} {r['offers']} -> " + " | ".join(f"{n}:{r['choices'][n]}{'' if (not r['rfc_reading'] or r['matches_reading'][n]) else '*'}" for n in IMPLS))
