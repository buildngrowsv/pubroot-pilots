#!/usr/bin/env python3
"""Build the outcome matrix and classify each outcome against a strict reading of RFC 9110 Section 14.
Classes: A = the outcome the RFC prescribes (SHOULD/MUST); P = a permitted alternative (ignore Range -> 200 full,
coalesce, or 416 for excessive/overlapping sets); L = lenient 206 for a syntactically invalid header;
R = 400/416 rejection of a syntactically invalid header (not prescribed); X = departs (416 for a satisfiable valid
request, 206 for an unsatisfiable one, a non-200 answer to an unknown unit, wrong window, or malformed Content-Range)."""
import json, os, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
IMPLS = ["express", "fastify_send", "starlette", "aiohttp", "werkzeug", "tornado", "go_net_http"]
cases = json.load(open(os.path.join(HERE, "cases.json")))
res = {n: {r["id"]: r for r in json.load(open(os.path.join(HERE, "results", f"{n}.json")))["rows"]} for n in IMPLS}
S = lambda w: {f"206 {w}"}
# expected (A) outcomes per case for the 100-byte file unless noted; kind decides how non-A outcomes are classed
EXP = {
 "R01": ("valid", S("0-9")), "R02": ("valid", S("10-19")), "R03": ("valid", S("0-0")), "R04": ("valid", S("99-99")),
 "R05": ("valid", S("50-99")), "R06": ("valid", S("90-99")), "R07": ("valid", S("0-99")), "R08": ("valid", S("0-99")),
 "R09": ("valid", S("0-99")), "R10": ("valid", S("0-99")),
 "R11": ("unsat", {"416 cr=bytes */100"}), "R12": ("unsat", {"416 cr=bytes */100"}), "R13": ("unsat", {"416 cr=bytes */100"}),
 "R14": ("unsat", {"416 cr=bytes */100"}),
 **{k: ("invalid", {"200 full"}) for k in ["R15","R16","R17","R18","R19","R20","R21","R22","R23","R30","R37","R38","R39","R40","R46","R47","R49","R53","R54"]},
 "R24": ("multi", {"206 multi[0-9,20-29]"}), "R25": ("multi", {"206 multi[0-9,5-14]", "206 0-14"}),
 "R26": ("multi", {"206 multi[0-9,10-19]", "206 0-19"}), "R27": ("multi", {"206 multi[20-29,0-9]", "206 multi[0-9,20-29]"}),
 "R28": ("valid", S("0-9")), "R29": ("unsat", {"416 cr=bytes */100"}),
 "R31": ("multi_excessive", {"206 0-9", "206 multi[0-9,0-9,0-9]"}), "R32": ("multi", {"206 multi[90-99,0-9]", "206 multi[0-9,90-99]"}),
 "R33": ("multi_excessive", {"206 multi[" + ",".join(f"{i}-{i}" for i in range(0, 40, 2)) + "]"}),
 "R34": ("valid", S("0-9")), "R35": ("valid", S("0-9")), "R36": ("unknown_unit", {"200 full"}),
 "R41": ("multi", {"206 multi[0-9,20-29]"}), "R42": ("multi", {"206 multi[0-9,20-29]"}), "R43": ("multi", {"206 multi[0-9,20-29]"}),
 "R44": ("valid", S("0-9")), "R45": ("valid", S("0-9")), "R48": ("valid", S("0-9")),
 "R50": ("valid", S("0-99")), "R51": ("unsat", {"416 cr=bytes */100"}), "R52": ("valid", S("0-99")),
 "R55": ("unsat", {"416 cr=bytes */0"}), "R56": ("unsat", {"416 cr=bytes */0"}),
 "R57": ("empty_suffix", {"200 full"}), "R58": ("unsat", {"416 cr=bytes */0"}),
}
def cls(c, out, ok):
    kind, exp = EXP[c["id"]]
    if out in exp and ok: return "A"
    if out.startswith("206 cr=") or not ok: return "X"
    if kind == "unknown_unit": return "X"
    if out == "200 full": return "P"
    if kind == "invalid": return "L" if out.startswith("206") else "R"
    if kind == "unsat": return "A" if out.startswith("416") else "X"
    if kind in ("multi_excessive",) and out.startswith("416"): return "P"
    if kind == "empty_suffix" and out.startswith("416"): return "P"
    return "X"
rows, tally = [], {n: dict(A=0, P=0, L=0, R=0, X=0) for n in IMPLS}
for c in cases:
    outs = {n: res[n][c["id"]]["outcome"] for n in IMPLS}; oks = {n: res[n][c["id"]]["body_ok"] for n in IMPLS}
    k = {n: cls(c, outs[n], oks[n]) for n in IMPLS}
    for n in IMPLS: tally[n][k[n]] += 1
    rows.append({**c, "expected": sorted(EXP[c["id"]][1]), "kind": EXP[c["id"]][0], "outcomes": outs, "class": k,
                 "n_distinct": len(set(outs.values()))})
pair = {f"{a}~{b}": sum(r["outcomes"][a] != r["outcomes"][b] for r in rows) for a, b in itertools.combinations(IMPLS, 2)}
summary = {"n_cases": len(rows), "n_impls": len(IMPLS), "cases_disagree_any": sum(r["n_distinct"] > 1 for r in rows),
           "max_distinct_outcomes": max(r["n_distinct"] for r in rows),
           "cases_all_A": sum(all(v == "A" for v in r["class"].values()) for r in rows),
           "class_tally": tally, "pairwise_disagreements": pair, "rows": rows}
gd = {r["id"]: r["outcome"] for r in json.load(open(os.path.join(HERE, "results", "go_godebug_maxranges1.json")))["rows"]}
summary["go_godebug_maxranges1_changed"] = sorted(i for i in gd if gd[i] != res["go_net_http"][i]["outcome"])
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1, sort_keys=True)
print(f"cases={len(rows)} disagree_any={summary['cases_disagree_any']} max_distinct={summary['max_distinct_outcomes']} all_A={summary['cases_all_A']}")
print("GODEBUG=httpservecontentmaxranges=1 changes Go on:", " ".join(summary["go_godebug_maxranges1_changed"]))
for n in IMPLS: print(f"  {n:13} " + " ".join(f"{k}={v}" for k, v in tally[n].items()))
for r in rows:
    print(f"{r['id']} {r['range'][:40]!r:42} " + " | ".join(f"{n}:{r['outcomes'][n]}[{r['class'][n]}]" for n in IMPLS))
