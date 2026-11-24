#!/usr/bin/env python3
"""Real-world sample: the distinct references in realworld/image_refs.json, classed per library against
distribution/reference (common.py). Run from the pilot directory after the runners are built (run_all.sh)."""
import json, subprocess, sys, collections
sys.path.insert(0, "."); from common import klass, norm, REF
snap = json.load(open("realworld/image_refs.json"))
strs = sorted({r["ref"] for r in snap["refs"]}); uses = collections.Counter(r["ref"] for r in snap["refs"])
cases = [dict(id=f"R{i:04d}", s=s) for i, s in enumerate(strs)]
json.dump(cases, open("realworld/rw_cases.json", "w"), indent=0)
PY = sys.argv[1] if len(sys.argv) > 1 else "python3"
out = {}
for cmd in ([PY, "py/run.py"], ["node", "js/run.mjs"], ["./.bin-go-refs"], ["./rs/target/release/rs-refs"]):
    out.update(json.loads(subprocess.run(cmd + ["realworld/rw_cases.json"], check=True, capture_output=True).stdout))
ref = out.pop(REF)
cls = {l: collections.Counter() for l in out}; ucls = {l: collections.Counter() for l in out}; dev = collections.defaultdict(list)
for c in cases:
    for l in out:
        k = klass(ref[c["id"]], out[l][c["id"]]); cls[l][k] += 1; ucls[l][k] += uses[c["s"]]
        if k != "A": dev[l].append(dict(s=c["s"], uses=uses[c["s"]], cls=k, ref=norm(ref[c["id"]]) if "ref" in ref[c["id"]] else None,
                                       lib=norm(out[l][c["id"]]) if "ref" in out[l][c["id"]] else out[l][c["id"]]["error"]))
rej = [c["s"] for c in cases if "error" in ref[c["id"]]]
hub = sum(norm(ref[c["id"]])[0] == "docker.io" for c in cases if "ref" in ref[c["id"]])
dig = sum(norm(ref[c["id"]])[3] is not None for c in cases if "ref" in ref[c["id"]])
res = dict(sources=snap["sources"], references=len(snap["refs"]), distinct=len(cases), templated_skipped=snap["skipped_templated"],
           reference_rejects=rej, docker_hub=hub, with_digest=dig, classes={l: dict(cls[l]) for l in out},
           classes_weighted_by_use={l: dict(ucls[l]) for l in out}, deviations={l: dev[l] for l in out})
json.dump(res, open("results/realworld.json", "w"), indent=1, ensure_ascii=False)
print(f"{res['references']} references, {len(cases)} distinct ({hub} on Docker Hub, {dig} with a digest); reference rejects {len(rej)}: {rej}")
for l in out: print(f"  {l:<28}", " ".join(f"{k}={cls[l][k]}" for k in "AWRL"), "| by use:", " ".join(f"{k}={ucls[l][k]}" for k in "AWRL"))
