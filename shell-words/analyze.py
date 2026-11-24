#!/usr/bin/env python3
"""Classes each splitter's output against the dash reading (results/sh_split.json), and each quoter's output by
whether dash (and bash --posix) turn it back into exactly the original string (results/sh_quote.json).
Split classes: A same argument vector; W different vector; R error where sh parses; L vector where sh reports a syntax error.
Scored groups: B S D E Q U L minus open cases. Shell-only groups (C O X) and open cases are tabulated separately."""
import json, collections, itertools
cases = json.load(open("cases.json")); Q = json.load(open("quote_cases.json"))
S = json.load(open("results/split.json")); SH = json.load(open("results/sh_split.json"))
QU = json.load(open("results/quote.json")); SHQ = json.load(open("results/sh_quote.json"))
LIBS = list(S)
def ref(cid): return SH["dash"][cid]
def klass(r, o):
    if "error" in r: return "A" if "error" in o else "L"
    if "error" in o: return "R"
    return "A" if o["argv"] == r["argv"] else "W"
rows = []; cnt = {l: collections.Counter() for l in LIBS}; cnt_sh = {l: collections.Counter() for l in LIBS}; cnt_open = {l: collections.Counter() for l in LIBS}
for c in cases:
    r = ref(c["id"]); row = dict(id=c["id"], s=c["s"], group=c["group"], scored=c["scored"], open=c.get("open"), dash=r, bash=SH["bash --posix"][c["id"]], out={}, cls={})
    for l in LIBS:
        o = S[l][c["id"]]; k = klass(r, o); row["out"][l] = o; row["cls"][l] = k
        (cnt if c["scored"] else cnt_open if c.get("open") else cnt_sh)[l][k] += 1
    rows.append(row)
sc = [r for r in rows if r["scored"]]
split_any = [r for r in rows if len({json.dumps(o, sort_keys=True) for o in r["out"].values()}) > 1]
dev = [r for r in sc if any(k != "A" for k in r["cls"].values())]
dash_bash = [r["id"] for r in rows if r["dash"].get("argv") != r["bash"].get("argv") or ("error" in r["dash"]) != ("error" in r["bash"])]
def vec(l): return [json.dumps(r["out"][l], sort_keys=True) for r in sc]
pair = {f"{a} vs {b}": sum(x != y for x, y in zip(vec(a), vec(b))) for a, b in itertools.combinations(LIBS, 2)}
# quoting
qrows = []; qcnt = {l: collections.Counter() for l in QU}
for q in Q:
    row = dict(id=q["id"], s=q["s"], quoted={}, cls={})
    for l in QU:
        o = QU[l][q["id"]]; row["quoted"][l] = o.get("argv", None)
        if "error" in o: k = "E"
        else:
            d, b = SHQ["dash"][l][q["id"]], SHQ["bash --posix"][l][q["id"]]
            ok_d, ok_b = d.get("argv") == [q["s"]] and "more_commands" not in d, b.get("argv") == [q["s"]] and "more_commands" not in b
            k = "OK" if ok_d and ok_b else ("FAIL" if not ok_d and not ok_b else ("FAIL-dash" if not ok_d else "FAIL-bash"))
            row.setdefault("sh", {})[l] = dict(dash=d, bash=b)
        row["cls"][l] = k; qcnt[l][k] += 1
    qrows.append(row)
summary = dict(n_cases=len(rows), n_scored=len(sc), n_any_split=len(split_any), n_scored_dev=len(dev), dash_vs_bash=dash_bash,
               classes={l: dict(cnt[l]) for l in LIBS}, classes_shell_only={l: dict(cnt_sh[l]) for l in LIBS}, classes_open={l: dict(cnt_open[l]) for l in LIBS}, pairwise_scored=pair,
               quote_classes={l: dict(qcnt[l]) for l in QU}, rows=rows, quote_rows=qrows)
json.dump(summary, open("results/summary.json", "w"), indent=1, ensure_ascii=False)
print(f"split cases {len(rows)} ({len(sc)} scored); outputs differ across libraries on {len(split_any)}; scored cases with a deviation from dash: {len(dev)}")
print("dash vs bash --posix differ on:", dash_bash)
print("classes on scored cases (A/W/R/L) | shell-only groups C O X (A/W/R/L) | open case E06:")
for l in LIBS: print(f"  {l:<20}", " ".join(f"{k}={cnt[l][k]}" for k in "AWRL"), "|", " ".join(f"{k}={cnt_sh[l][k]}" for k in "AWRL"), "|", "".join(k for k in "AWRL" if cnt_open[l][k]))
print("pairwise differences on scored cases: min", min(pair.values()), "max", max(pair.values()))
print("quote round trip (OK/FAIL/FAIL-dash/FAIL-bash/E):")
for l in QU: print(f"  {l:<20}", " ".join(f"{k}={qcnt[l][k]}" for k in ("OK", "FAIL", "FAIL-dash", "FAIL-bash", "E")))
for r in rows:
    print(f"{r['id']} {r['s']!r} dash={r['dash'].get('argv', 'ERROR')}")
    print("   ", "; ".join(f"{l}={r['cls'][l]}" + ("" if r["cls"][l] == "A" else f":{r['out'][l].get('argv', 'ERR')}") for l in LIBS))
for r in qrows:
    print(f"{r['id']} {r['s']!r}: " + "; ".join(f"{l}={r['cls'][l]}" + ("" if r["cls"][l] == "OK" else f":{r['quoted'][l]!r}") for l in QU))
