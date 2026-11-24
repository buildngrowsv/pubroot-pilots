#!/usr/bin/env python3
"""Classes every library result against distribution/reference (results/refs.json); see common.py.
N15 is open: for "a-b_c.d/e--f" the reference returns an empty registry and keeps the whole string as the path
(its domain split picks "a-b_c.d" as a host, which then fails the host pattern), which is not a usable reading."""
import json, collections, itertools
from common import klass, norm, REF
OPEN = {"N15": "reference returns an empty registry"}
cases = json.load(open("cases.json")); R = json.load(open("results/refs.json"))
LIBS = [l for l in R if l != REF]; rows = []; cnt = {l: collections.Counter() for l in LIBS}
for c in cases:
    r = R[REF][c["id"]]; row = dict(id=c["id"], s=c["s"], group=c["group"], open=OPEN.get(c["id"]), ref=r, out={}, cls={})
    for l in LIBS:
        o = R[l][c["id"]]; k = klass(r, o); row["out"][l] = o; row["cls"][l] = k
        if c["id"] not in OPEN: cnt[l][k] += 1
    rows.append(row)
sc = [r for r in rows if not r["open"]]
def outc(o): return "ERROR" if "error" in o else json.dumps(norm(o))
dev = [r for r in sc if any(k != "A" for k in r["cls"].values())]
any_split = [r for r in rows if len({outc(o) for o in r["out"].values()} | {outc(r["ref"])}) > 1]
pair = {f"{a} vs {b}": sum(outc(r["out"][a]) != outc(r["out"][b]) for r in sc) for a, b in itertools.combinations(LIBS, 2)}
json.dump(dict(n_cases=len(rows), n_scored=len(sc), n_any_differs=len(any_split), n_scored_dev=len(dev),
               classes={l: dict(cnt[l]) for l in LIBS}, pairwise_scored=pair, rows=rows), open("results/summary.json", "w"), indent=1, ensure_ascii=False)
print(f"cases {len(rows)} ({len(sc)} scored); some library differs from the reference on {len(any_split)}; scored cases with a deviation: {len(dev)}")
print("classes on scored cases (A/W/R/L) | N15:")
for l in LIBS: print(f"  {l:<28}", " ".join(f"{k}={cnt[l][k]}" for k in "AWRL"), "|", rows[[r['id'] for r in rows].index('N15')]["cls"][l])
print("pairwise differences on scored cases: min", min(pair.values()), "max", max(pair.values()))
for r in rows:
    print(f"{r['id']}{' (open)' if r['open'] else ''} {r['s']!r} ref={norm(r['ref']) if 'ref' in r['ref'] else 'ERROR'}")
    print("   ", "; ".join(f"{l}={r['cls'][l]}" + ("" if r["cls"][l] == "A" else ":" + (json.dumps(norm(r['out'][l])) if 'ref' in r['out'][l] else 'ERR')) for l in LIBS))
