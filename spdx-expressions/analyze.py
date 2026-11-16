#!/usr/bin/env python3
"""Merges results/{node,py,go,rs}.json, compares each implementation with the Annex B reading in cases.json
and with each other. Writes results/summary.json and prints the report (results/report.txt).
Readings: tree implementations (spdx-expression-parse 5 and 3, license-expression, spdx-rs) are rendered as
flattened S-expressions; packaging and go-spdx expose no tree, so they are compared on acceptance and on the
leaf set (tokens of each library's canonical string). go-spdx ExtractLicenses is recorded separately because it
can fail on an expression that ValidateAndNormalizeLicensesWithOptions accepts.
Class per case and implementation: A agrees; N accepted but rewrote an identifier to its current SPDX equivalent;
T accepted with a different tree; R rejected a valid expression; L accepted an invalid expression; - spec silent."""
import json, re, collections
cases = json.load(open("cases.json"))
R = {}
for f in ("node", "py", "go", "rs"):
    d = json.load(open(f"results/{f}.json")); d.pop("_list_version", None); R.update(d)
TREE = ["spdx-expression-parse@5", "spdx-expression-parse@3", "license-expression", "spdx-rs"]
FLAT = ["packaging", "go-spdx"]
IMPLS = TREE + FLAT
PROBERS = ["spdx-satisfies@6", "go-spdx", "spdx-rs"]
# SPDX License List deprecations: deprecated id -> current equivalent (used only to label class N)
ALIAS = {"gpl-2.0": "gpl-2.0-only", "gpl-2.0+": "gpl-2.0-or-later", "lgpl-2.1+": "lgpl-2.1-or-later",
         "gpl-3.0": "gpl-3.0-only", "gpl-2.0-or-later+": "gpl-2.0-or-later",
         "gpl-2.0-with-classpath-exception": "gpl-2.0-only with classpath-exception-2.0",
         "wxwindows": "lgpl-2.0-or-later with wxwindows-exception-3.1",
         "gpl-2.0-only with nokia-qt-exception-1.1": "gpl-2.0-only with qt-lgpl-exception-1.1"}
def flat(t):
    if isinstance(t, str): return t
    op, kids = t[0], []
    for k in t[1:]:
        k = flat(k)
        if isinstance(k, list) and k[0] == op: kids += k[1:]
        else: kids.append(k)
    return [op] + kids
def render(t): return t if isinstance(t, str) else "(" + t[0] + " " + " ".join(render(k) for k in t[1:]) + ")"
def parse_expect(s):  # expected trees are written in the same S-expression syntax
    toks = re.findall(r"\(|\)|[^\s()]+(?: WITH [^\s()]+)?", s)
    def p(i):
        if toks[i] == "(":
            op = toks[i + 1]; i += 2; kids = []
            while toks[i] != ")": k, i = p(i); kids.append(k)
            return [op] + kids, i + 1
        return toks[i], i + 1
    return p(0)[0]
def leaves(t): return [t] if isinstance(t, str) else [x for k in t[1:] for x in leaves(k)]
def cf(x): return x.casefold()
def al(x): return ALIAS.get(cf(x), cf(x))
def tmap(t, f): return f(t) if isinstance(t, str) else [t[0]] + [tmap(k, f) for k in t[1:]]
def canon_leaves(s):
    s = s.replace("(", " ").replace(")", " "); toks = s.split(); out = []; i = 0
    while i < len(toks):
        if toks[i] in ("AND", "OR"): i += 1; continue
        if i + 2 < len(toks) + 0 and i + 1 < len(toks) and toks[i + 1] == "WITH": out.append(f"{toks[i]} WITH {toks[i + 2]}"); i += 3; continue
        out.append(toks[i]); i += 1
    return out
def reading(impl, cid):
    r = R[impl][cid]
    if not r.get("ok"): return None
    if impl in TREE: return flat(r["tree"])
    return sorted(set(canon_leaves(r["canon"])))  # packaging and go-spdx: leaves of the library's canonical string
rows, cls_count = [], {i: collections.Counter() for i in IMPLS}
for c in cases:
    cid, exp = c["id"], c["expect"]
    row = dict(id=cid, group=c["group"], expr=c["expr"], expect=exp, out={}, cls={})
    for i in IMPLS:
        rd = reading(i, cid)
        if rd is None: row["out"][i] = "REJECT"
        elif i in TREE: row["out"][i] = render(rd)
        elif i == "packaging": row["out"][i] = R[i][cid]["canon"]
        else: row["out"][i] = R[i][cid].get("canon", "{" + ", ".join(rd) + "}")
        if exp == "OPEN": k = "-"
        elif exp == "INVALID": k = "A" if rd is None else "L"
        elif rd is None: k = "R"
        else:
            et = flat(parse_expect(exp))
            if i in TREE:
                if tmap(rd, cf) == tmap(et, cf): k = "A"
                elif tmap(rd, al) == tmap(et, al): k = "N"
                else: k = "T"
            else:
                got = sorted(set(map(cf, rd))); want = sorted(set(map(cf, leaves(et))))
                k = "A" if got == want else "N" if sorted(set(map(al, rd))) == sorted(set(map(al, leaves(et)))) else "T"
        row["cls"][i] = k; cls_count[i][k] += 1
    # cross-implementation disagreement on acceptance, and on meaning among accepting implementations
    acc = {i: row["out"][i] != "REJECT" for i in IMPLS}
    row["accept_split"] = len(set(acc.values())) > 1
    mean = set()
    for i in IMPLS:
        rd = reading(i, cid)
        if rd is None: continue
        mean.add(json.dumps(sorted(set(map(al, rd if i in FLAT else leaves(rd))))))
    trees = {json.dumps(tmap(reading(i, cid), al)) for i in TREE if reading(i, cid) is not None}
    row["leaf_split"] = len(mean) > 1; row["tree_split"] = len(trees) > 1
    row["probes"] = {p: R[p].get(cid, {}).get("probes") for p in PROBERS if c["probes"]}
    row["probe_expect"] = [p["sat"] for p in c["probes"]]
    row["distinct"] = len({row["out"][i] if row["out"][i] == "REJECT" else "ACC" for i in IMPLS}) + max(0, len(mean) - 1)
    rows.append(row)
n = len(rows)
acc_split = [r for r in rows if r["accept_split"]]
any_split = [r for r in rows if r["accept_split"] or r["leaf_split"] or r["tree_split"]]
pw = {}
for a in IMPLS:
    for b in IMPLS:
        if a < b: pw[f"{a} vs {b}"] = sum((r["out"][a] == "REJECT") != (r["out"][b] == "REJECT") for r in rows)
probe_fail = {p: [r["id"] for r in rows if r["probes"] and r["probes"].get(p) is not None and r["probes"][p] != r["probe_expect"]] for p in PROBERS}
go_internal = {"validate_ok_extract_fails": [r["id"] for r in rows if R["go-spdx"][r["id"]].get("ok") and "extract_err" in R["go-spdx"][r["id"]]],
               "validate_fails_extract_ok": [r["id"] for r in rows if not R["go-spdx"][r["id"]].get("ok") and "leaves" in R["go-spdx"][r["id"]]]}
summary = dict(go_validate_vs_extract=go_internal, n_cases=n, n_accept_split=len(acc_split), n_any_split=len(any_split),
               n_leaf_split=sum(r["leaf_split"] for r in rows), n_tree_split=sum(r["tree_split"] for r in rows),
               classes={i: dict(sorted(cls_count[i].items())) for i in IMPLS},
               pairwise_accept_disagreement=pw, probe_mismatch=probe_fail, rows=rows)
json.dump(summary, open("results/summary.json", "w"), indent=1, ensure_ascii=False)
print(f"cases {n}; acceptance split {len(acc_split)}; any split (acceptance, leaves or tree) {len(any_split)}; "
      f"leaf split {summary['n_leaf_split']}; tree split {summary['n_tree_split']}")
print("classes A/N/T/R/L/-:")
for i in IMPLS: print(f"  {i:<26}", " ".join(f"{k}{cls_count[i][k]}" for k in "ANTRL-"))
print("probe mismatches vs spec precedence:", probe_fail)
print("go-spdx ValidateAndNormalizeLicensesWithOptions vs ExtractLicenses:", go_internal)
print("pairwise acceptance disagreement:", min(pw.values()), "-", max(pw.values()))
for k, v in sorted(pw.items(), key=lambda x: -x[1]): print(f"  {k}: {v}")
print()
print("id | expr | expect | " + " | ".join(IMPLS))
for r in rows: print(f"{r['id']} | {r['expr']!r} | {r['expect']} | " + " | ".join(f"{r['cls'][i]}:{r['out'][i]}" for i in IMPLS))

# real-world sample (no expected reading; acceptance and leaf agreement only)
RW = {}
for f in ("node", "py", "go", "rs"):
    d = json.load(open(f"results/rw_{f}.json")); d.pop("_list_version", None); RW.update(d)
rw = json.load(open("rw_cases.json")); R = RW
print()
print(f"real-world sample: {len(rw)} distinct strings from {sum(c['packages'] for c in rw)} packages")
rw_rows = []
for c in rw:
    accs = {i: RW[i][c["id"]]["ok"] for i in IMPLS}
    lv = {json.dumps(sorted(set(map(al, reading(i, c["id"]) if i in FLAT else leaves(reading(i, c["id"])))))) for i in IMPLS if accs[i]}
    raw = {json.dumps(sorted(set(map(cf, reading(i, c["id"]) if i in FLAT else leaves(reading(i, c["id"])))))) for i in IMPLS if accs[i]}
    rw_rows.append(dict(id=c["id"], expr=c["expr"], packages=c["packages"], accept=accs, leaf_split=len(lv) > 1, rewrite=len(raw) > 1))
    if not all(accs.values()) or len(raw) > 1:
        print(f"  {c['id']} {c['expr']!r} packages={c['packages']} rejected_by={[i for i in IMPLS if not accs[i]]} rewritten={len(raw) > 1}")
print(f"  unanimous: {sum(all(r['accept'].values()) and not r['rewrite'] for r in rw_rows)}/{len(rw_rows)} strings")
json.dump(rw_rows, open("results/rw_summary.json", "w"), indent=1)
