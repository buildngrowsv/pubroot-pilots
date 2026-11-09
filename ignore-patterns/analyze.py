#!/usr/bin/env python3
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(HERE, "cases", "meta.json")))
git = json.load(open(os.path.join(HERE, "results", "git.json")))
moby = json.load(open(os.path.join(HERE, "results", "moby.json")))
balena = json.load(open(os.path.join(HERE, "results", "balena.json")))
paths = [p for p,_ in meta["paths"]]
rows = []
disagree_gm = disagree_gb = disagree_mb = 0
case_disagree_gm = 0
for name in meta["pattern_names"]:
    g, m, b = git[name], moby[name], balena[name]
    diffs = []
    for p in paths:
        gv, mv, bv = bool(g.get(p)), bool(m.get(p)), bool(b.get(p))
        if gv != mv or gv != bv or mv != bv:
            diffs.append(dict(path=p, git=gv, moby=mv, balena=bv))
        if gv != mv: disagree_gm += 1
        if gv != bv: disagree_gb += 1
        if mv != bv: disagree_mb += 1
    if any(bool(g.get(p)) != bool(m.get(p)) for p in paths):
        case_disagree_gm += 1
    rows.append(dict(case=name, n_diff_any=len(diffs), diffs=diffs))
summary = dict(
    n_cases=len(meta["pattern_names"]),
    n_paths=len(paths),
    path_verdicts=len(meta["pattern_names"])*len(paths),
    cases_git_vs_moby_disagree=case_disagree_gm,
    path_cells_git_vs_moby=disagree_gm,
    path_cells_git_vs_balena=disagree_gb,
    path_cells_moby_vs_balena=disagree_mb,
    cases=rows,
)
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=2)
print(json.dumps({k:summary[k] for k in summary if k!='cases'}, indent=2))
# show a few interesting diffs
for r in rows:
    if r["n_diff_any"]:
        print(r["case"], r["n_diff_any"], r["diffs"][:3])
