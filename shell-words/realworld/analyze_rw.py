#!/usr/bin/env python3
"""Real-world sample: the distinct script strings in realworld/npm_scripts.json. npm runs these with sh -c on POSIX
systems, so dash's reading is the reference. "Plain" strings are those with no character that brings in shell syntax
beyond quoting and word splitting: ; | & < > ( ) $ ` newline, a # or ~ (comments, tilde), glob characters * ? [ ],
and braces. On plain strings each library is classed against dash; on all strings, libraries are compared with each other.
Run from the pilot directory after the split runners exist (run_all.sh calls it)."""
import json, subprocess, sys, collections, re
snap = json.load(open("realworld/npm_scripts.json"))
strs = sorted({s for p in snap["packages"] for s in p["scripts"].values() if isinstance(s, str)})
SPECIAL = re.compile(r"[;|&<>()$`\n#~*?\[\]{}]")
cases = [dict(id=f"N{i:04d}", s=s, group="npm", scored=not SPECIAL.search(s), open=None) for i, s in enumerate(strs)]
json.dump(cases, open("realworld/rw_cases.json", "w"), ensure_ascii=False, indent=0)
PY = sys.argv[1] if len(sys.argv) > 1 else "python3"
out = {}
for cmd in ([PY, "py/run.py"], ["node", "js/run.mjs"], ["./.bin-go-words"], ["./rs/target/release/rs-words"]):
    out.update(json.loads(subprocess.run(cmd + ["split", "realworld/rw_cases.json"], check=True, capture_output=True).stdout))
sh = json.loads(subprocess.run(["python3", "oracle.py", "split", "realworld/rw_cases.json"], check=True, capture_output=True).stdout)
plain = [c for c in cases if c["scored"]]
cls = {l: collections.Counter() for l in out}; ex = collections.defaultdict(list)
for c in plain:
    r = sh["dash"][c["id"]]
    for l in out:
        o = out[l][c["id"]]
        k = ("A" if "error" in o else "L") if "error" in r else ("R" if "error" in o else ("A" if o["argv"] == r["argv"] else "W"))
        cls[l][k] += 1
        if k != "A": ex[l].append(dict(s=c["s"], dash=r.get("argv"), lib=o.get("argv", o.get("error"))))
dashbash = sum(sh["dash"][c["id"]] != sh["bash --posix"][c["id"]] for c in plain)
allagree = sum(len({json.dumps(out[l][c["id"]], sort_keys=True) for l in out}) == 1 for c in cases)
# which special characters make strings non-plain
why = collections.Counter(ch for c in cases if not c["scored"] for ch in set(SPECIAL.findall(c["s"])))
quoted_plain = sum(bool(re.search(r"[\\'\"]", c["s"])) for c in plain)
OPS = re.compile(r"&&|\|\||[;|&<>]")
opstr = [c for c in cases if OPS.search(c["s"])]
op_err = {l: sum("error" in out[l][c["id"]] for c in opstr) for l in out}
mv_rej = [c for c in cases if "error" in out["mvdan sh Fields"][c["id"]]]
tok_on_rej = {l: sum("argv" in out[l][c["id"]] for c in mv_rej) for l in out}
res = dict(mvdan_rejected=len(mv_rej), vectors_returned_on_mvdan_rejected=tok_on_rej, plain_with_quote_or_backslash=quoted_plain, with_operator=len(opstr), errors_on_operator_strings=op_err, source=snap["source"], packages=len(snap["packages"]), packages_with_scripts=sum(bool(p["scripts"]) for p in snap["packages"]),
           distinct_strings=len(cases), plain=len(plain), dash_vs_bash_on_plain=dashbash,
           all_libraries_identical_all_strings=allagree, special_char_counts=dict(sorted(why.items(), key=lambda kv: (-kv[1], kv[0]))),
           classes_plain={l: dict(cls[l]) for l in out}, deviations_plain={l: ex[l] for l in out})
json.dump(res, open("results/realworld.json", "w"), indent=1, ensure_ascii=False)
print(f"{res['packages']} packages ({res['packages_with_scripts']} with scripts), {len(cases)} distinct strings, {len(plain)} plain; dash vs bash differ on {dashbash} plain")
print(f"plain strings with a quote or backslash: {quoted_plain}; strings containing ; | & < > (quoted or not): {len(opstr)}; errors on those:", op_err)
print(f"mvdan's parser rejects {len(mv_rej)} strings; argument vectors returned for those:", tok_on_rej)
print(f"all libraries give the same output on {allagree} of {len(cases)} strings")
for l in out: print(f"  {l:<20}", " ".join(f"{k}={cls[l][k]}" for k in "AWRL"))
