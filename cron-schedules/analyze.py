#!/usr/bin/env python3
"""Merges results/{py,node,go}.json, compares each library with the crontab(5) reading and with each other.
Class per case and library: A agrees; S accepted but a different schedule (any of the first N times differs);
R rejected a valid expression; L accepted an invalid expression (L0 = accepted it but returns no fire time);
T timed out; - reading is OPEN. Writes results/summary.json; prints the report."""
import json, collections
D = json.load(open("cases.json")); R = {}
for f in ("py", "node", "go"): R.update(json.load(open(f"results/{f}.json")))
IMPLS = ["croniter", "cronsim", "apscheduler", "cron-parser", "croner", "cron", "robfig-cron", "gronx", "cronexpr"]
def out(i, cid):
    r = R[i][cid]
    if not r["ok"]: return "TIMEOUT" if r["err"] == "TIMEOUT" else "REJECT"
    return " ".join(r["times"]) if r["times"] else "NONE"
rows, cc = [], {i: collections.Counter() for i in IMPLS}
for c in D["cases"]:
    exp = c["expect"]; row = dict(id=c["id"], group=c["group"], expr=c["expr"], expect=exp, out={}, cls={})
    for i in IMPLS:
        o = out(i, c["id"]); row["out"][i] = o
        if exp == "OPEN": k = "-"
        elif o == "TIMEOUT": k = "T"
        elif exp == "INVALID": k = "A" if o == "REJECT" else ("L0" if o == "NONE" else "L")
        elif exp == "NEVER": k = "A" if o in ("REJECT", "NONE") else "S"
        elif o == "REJECT": k = "R"
        else: k = "A" if o == " ".join(exp) else "S"
        row["cls"][i] = k; cc[i][k] += 1
    row["distinct"] = len(set(row["out"].values()))
    rows.append(row)
n = len(rows); dis = [r for r in rows if r["distinct"] > 1]
pw = {f"{a} vs {b}": sum(r["out"][a] != r["out"][b] for r in rows) for a in IMPLS for b in IMPLS if a < b}
summary = dict(n_cases=n, start=D["start"], n_times=D["n"], n_disagree=len(dis), max_distinct=max(r["distinct"] for r in rows),
               n_unanimous=n - len(dis), classes={i: dict(sorted(cc[i].items())) for i in IMPLS}, pairwise=pw, rows=rows)
json.dump(summary, open("results/summary.json", "w"), indent=1)
print(f"cases {n}; start {D['start']}; first {D['n']} fire times; disagree {len(dis)}; unanimous {n - len(dis)}; max distinct outputs {summary['max_distinct']}")
print("classes A/S/R/L/L0/T/-:")
for i in IMPLS: print(f"  {i:<12}", " ".join(f"{k}={cc[i][k]}" for k in ("A", "S", "R", "L", "L0", "T", "-")))
ext = [r for r in rows if r["group"] == "extension"]
summary["extension_support"] = {r["expr"]: [i for i in IMPLS if r["out"][i] not in ("REJECT", "TIMEOUT")] for r in ext}
json.dump(summary, open("results/summary.json", "w"), indent=1)
print("extension support (accepting libraries):")
for k, v in summary["extension_support"].items(): print(f"  {k!r}: {len(v)} {v}")
nonopen = [r for r in rows if r["expect"] != "OPEN"]
print(f"cases with a reading: {len(nonopen)}; of which disagree {sum(r['distinct'] > 1 for r in nonopen)}")
print("pairwise disagreement:", min(pw.values()), "-", max(pw.values()))
for k, v in sorted(pw.items(), key=lambda x: (-x[1], x[0])): print(f"  {k}: {v}")
print()
for r in rows:
    print(f"{r['id']} {r['expr']!r} expect={r['expect'] if isinstance(r['expect'], str) else r['expect'][:2]}")
    for i in IMPLS: print(f"    {i:<12} {r['cls'][i]:<2} {r['out'][i][:60]}")

# real-world sample (GitHub Actions schedules; committed snapshot realworld/gha_cron.json)
RWD = json.load(open("rw_cases.json")); RR = {}
for f in ("py", "node", "go"): RR.update(json.load(open(f"results/rw_{f}.json")))
R = RR
rw = []
for c in RWD["cases"]:
    outs = {i: out(i, c["id"]) for i in IMPLS}
    exp = c["expect"]; ok = {i: True if exp == "OPEN" else (outs[i] == "REJECT") if exp == "INVALID" else (outs[i] == " ".join(exp)) for i in IMPLS}
    rw.append(dict(id=c["id"], expr=c["expr"], files=c["files"], expect=exp, distinct=len(set(outs.values())), deviating=[i for i in IMPLS if not ok[i]]))
json.dump(rw, open("results/rw_summary.json", "w"), indent=1)
d = [r for r in rw if r["distinct"] > 1]
print()
print(f"real-world sample: {len(rw)} distinct GitHub Actions schedule expressions from {sum(r['files'] for r in rw)} expression-file pairs")
print(f"  disagree: {len(d)} expressions ({sum(r['files'] for r in d)} file occurrences); invalid per crontab(5): {sum(r['expect'] == 'INVALID' for r in rw)}; reading open: {sum(r['expect'] == 'OPEN' for r in rw)}")
dev = collections.Counter(i for r in rw for i in r["deviating"])
print("  expressions where a library deviates from the crontab(5) reading:", dict(dev))
for r in d: print(f"  {r['id']} {r['expr']!r} files={r['files']} deviating={r['deviating']}")
