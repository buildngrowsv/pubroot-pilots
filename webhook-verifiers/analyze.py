#!/usr/bin/env python3
"""Summarise results/rep*/*.jsonl into results/summary.json and results/matrix.md."""
import json, glob, os, sys, collections
R = sys.argv[1] if len(sys.argv) > 1 else "results"
reps = sorted(glob.glob(f"{R}/rep*"))
data = {}
for rp in reps:
    rows = [json.loads(l) for f in sorted(glob.glob(f"{rp}/*.jsonl")) for l in open(f) if l.strip()]
    data[os.path.basename(rp)] = {(r["runtime"].split()[0] if "workerd" not in r["runtime"] else "workerd", r["subject"], r["case"]): r for r in rows}
r1 = data[os.path.basename(reps[0])]
stable = all(all(d.get(k, {}).get("verdict") == v["verdict"] for k, v in r1.items()) and len(d) == len(r1) for d in data.values())
subj = sorted({(k[0], k[1]) for k in r1})
runtimes = {k[0]: v["runtime"] for k, v in r1.items()}
cases = {}
for (rt, s, c), v in r1.items(): cases.setdefault(c, dict(scheme=v["scheme"], cls=v["cls"], ref=v["ref"]))
summ = dict(reps=len(reps), stable_across_reps=stable, rows_per_rep=len(r1), cases=len(cases), runtimes=runtimes, subjects={})
for rt, s in subj:
    rows = [v for (a, b, c), v in r1.items() if a == rt and b == s]
    ctl = [v for v in rows if v["cls"] in ("control", "parsing", "config") and v["ref"] != "unspecified"]
    summ["subjects"][f"{rt}: {s}"] = dict(
        rows=len(rows), graded=len(ctl),
        agree=sum(v["verdict"] == v["ref"] for v in ctl),
        over_accept=[v["case"] for v in ctl if v["ref"] == "reject" and v["verdict"] == "accept"],
        under_accept=[v["case"] for v in ctl if v["ref"] == "accept" and v["verdict"] != "accept"],
        crash=[v["case"] for v in rows if v["verdict"] == "crash"],
        canon_accept=[v["case"] for v in rows if v["cls"] == "canonicalization" and v["verdict"] == "accept"])
# disagreements: same case, different verdicts among subjects/runtimes
dis = {}
for c in cases:
    vs = {f"{a}: {b}": v["verdict"] for (a, b, cc), v in r1.items() if cc == c}
    if len(set(vs.values())) > 1: dis[c] = vs
summ["disagreeing_cases"] = len(dis); summ["disagreements"] = dis
json.dump(summ, open(f"{R}/summary.json", "w"), indent=1)
# markdown matrix
cols = [f"{a}: {b}" for a, b in subj]
L = [f"# Verdict matrix ({len(reps)} reps, stable={stable}; A=accept, r=reject, X=crash, .=not run)\n", "| case | cls | ref | " + " | ".join(cols) + " |", "|" + "---|" * (3 + len(cols))]
for c, m in sorted(cases.items()):
    cells = []
    for a, b in subj:
        v = r1.get((a, b, c)); cells.append("." if not v else {"accept": "A", "reject": "r", "crash": "X"}[v["verdict"]])
    L.append(f"| {c} | {m['cls']} | {m['ref']} | " + " | ".join(cells) + " |")
open(f"{R}/matrix.md", "w").write("\n".join(L) + "\n")
print(json.dumps({k: summ[k] for k in ("reps", "stable_across_reps", "rows_per_rep", "cases", "disagreeing_cases")}))
for k, v in summ["subjects"].items(): print(f"{k:<55} graded {v['graded']:>2} agree {v['agree']:>2} over {len(v['over_accept'])} under {len(v['under_accept'])} crash {len(v['crash'])} canon_acc {len(v['canon_accept'])}")
# secondary: disagreements when the documented-unsupported pairing (sync constructEvent on Bun/workerd) is excluded
ex = {c: {k: v for k, v in vs.items() if not (k.endswith("js-stripe constructEvent") and not k.startswith("Node"))} for c, vs in dis.items()}
ex = {c: vs for c, vs in ex.items() if len(set(vs.values())) > 1}
summ["disagreeing_cases_excl_sync_stripe_on_web_runtimes"] = len(ex)
json.dump(summ, open(f"{R}/summary.json", "w"), indent=1)
print("disagreeing excl. sync stripe on Bun/workerd:", len(ex), sorted(ex))
