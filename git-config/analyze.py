#!/usr/bin/env python3
"""Classes each library's reading of every case against git's (results/git.json); see common.py for the classes.
Open cases (not scored): K09 (a key before any section header) and V19 (a backslash at the very end of the file);
git's documentation does not say what either means, and git's own reading is shown for reference."""
import json, collections, itertools
from common import klass, norm
OPEN = {"K09": "key before any section header", "V19": "backslash as the last byte of the file"}
cases = json.load(open("cases.json")); G = json.load(open("results/git.json")); L = json.load(open("results/libs.json"))
LIBS = list(L); rows = []; cnt = {l: collections.Counter() for l in LIBS}; cnt_open = {l: collections.Counter() for l in LIBS}
for c in cases:
    r = G[c["id"]]; row = dict(id=c["id"], text=c["text"], group=c["group"], open=OPEN.get(c["id"]), git=r, out={}, cls={})
    for l in LIBS:
        o = L[l][c["id"]]; k = klass(r, o); row["out"][l] = o; row["cls"][l] = k
        (cnt_open if c["id"] in OPEN else cnt)[l][k] += 1
    rows.append(row)
sc = [r for r in rows if not r["open"]]
dev = [r for r in sc if any(k not in "A" for k in r["cls"].values())]
devW = [r for r in sc if any(k in "WRL" for k in r["cls"].values())]
def outc(o): return "ERROR" if "error" in o else json.dumps(sorted(norm(o).items()))
any_split = [r for r in rows if len({outc(o) for o in r["out"].values()} | {outc(r["git"])}) > 1]
pair = {f"{a} vs {b}": sum(outc(r["out"][a]) != outc(r["out"][b]) for r in sc) for a, b in itertools.combinations(LIBS, 2)}
summary = dict(n_cases=len(rows), n_scored=len(sc), n_any_differs_from_git_or_each_other=len(any_split), n_scored_any_non_A=len(dev),
               n_scored_any_WRL=len(devW), classes={l: dict(cnt[l]) for l in LIBS}, classes_open={l: dict(cnt_open[l]) for l in LIBS},
               pairwise_scored=pair, rows=rows)
json.dump(summary, open("results/summary.json", "w"), indent=1, ensure_ascii=False)
print(f"cases {len(rows)} ({len(sc)} scored); some library differs from git on {len(any_split)}; scored cases with any non-A: {len(dev)}, with any W/R/L: {len(devW)}")
print("classes on scored cases (A/T/W/R/L) | open cases K09 V19:")
for l in LIBS: print(f"  {l:<18}", " ".join(f"{k}={cnt[l][k]}" for k in "ATWRL"), "|", " ".join(f"{r['id']}={r['cls'][l]}" for r in rows if r["open"]))
print("pairwise differences on scored cases: min", min(pair.values()), "max", max(pair.values()))
for r in rows:
    g = r["git"]; print(f"{r['id']}{' (open)' if r['open'] else ''} {r['text']!r}\n   git={g.get('entries', 'ERROR')}")
    print("   ", "; ".join(f"{l}={r['cls'][l]}" + ("" if r["cls"][l] == "A" else ":" + (json.dumps(r['out'][l]['entries'], ensure_ascii=False) if 'entries' in r['out'][l] else 'ERR ' + r['out'][l]['error'][:60])) for l in LIBS))
