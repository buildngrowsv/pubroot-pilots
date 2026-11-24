#!/usr/bin/env python3
"""Real-world sample: each git config file in realworld/snapshot.local.json (rebuild it with
`python3 realworld/fetch_gitconfigs.py --restore` from the committed list) is read by git and by every library.
Per file and library: class (common.py) and the keys whose values differ. Values are not written out, because the
files are personal configuration. Run from the pilot directory with the library outputs available (run_all.sh)."""
import json, subprocess, sys, collections, os
sys.path.insert(0, "."); from common import klass, diff_keys, norm
snap = json.load(open("realworld/snapshot.local.json"))
cases = [dict(id=f"F{i:02d}", text=f["text"], group="real") for i, f in enumerate(snap["files"])]
tmp = "realworld/.rw_cases.local.json"; json.dump(cases, open(tmp, "w"))
PY = sys.argv[1] if len(sys.argv) > 1 else "python3"
out = {}
for cmd in ([PY, "py/run.py"], ["node", "js/run.mjs"], ["./.bin-go-gc"], ["./rs/target/release/rs-gitconfig"]):
    out.update(json.loads(subprocess.run(cmd + [tmp], check=True, capture_output=True).stdout))
G = json.loads(subprocess.run(["python3", "oracle.py", tmp], check=True, capture_output=True).stdout)
os.remove(tmp)
cls = {l: collections.Counter() for l in out}; files = []; keydev = {l: collections.Counter() for l in out}
n_entries = sum(len(G[c["id"]].get("entries", [])) for c in cases)
for c, f in zip(cases, snap["files"]):
    row = dict(file=f"{f['repo']}@{f['commit'][:12]}:{f['path']}", git_ok="entries" in G[c["id"]],
               git_entries=len(G[c["id"]].get("entries", [])), cls={}, keys={})
    for l in out:
        k = klass(G[c["id"]], out[l][c["id"]]); cls[l][k] += 1; row["cls"][l] = k
        if k == "W": dk = diff_keys(G[c["id"]], out[l][c["id"]]); row["keys"][l] = dk; keydev[l][c["id"]] = len(dk)
        if k == "R": row["keys"][l] = "error: " + out[l][c["id"]]["error"][:120]
    files.append(row)
res = dict(source=snap["source"], files=len(cases), git_entries=n_entries, git_rejects=sum(not r["git_ok"] for r in files),
           classes={l: dict(cls[l]) for l in out}, keys_differing={l: sum(keydev[l].values()) for l in out}, per_file=files)
json.dump(res, open("results/realworld.json", "w"), indent=1, ensure_ascii=False)
print(f"{len(cases)} files, {n_entries} entries as read by git; git rejects {res['git_rejects']}")
for l in out: print(f"  {l:<18}", " ".join(f"{k}={cls[l][k]}" for k in "ATWRL"), f"| keys differing: {res['keys_differing'][l]}")
