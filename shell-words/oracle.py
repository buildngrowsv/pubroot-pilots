#!/usr/bin/env python3
"""POSIX sh reference: run each string as the arguments of a shell function in dash and in bash --posix, with an
empty environment (env -i; PATH and HOME point nowhere), globbing off (set -f), inside a throwaway directory. The function
writes its arguments NUL-separated to fd 3, one record per call, so later commands on the same line (after ; | & or a
newline) are visible as extra records. Usage: oracle.py split|quote IN.json [QUOTED.json] > out.json
split: IN = cases.json. quote: IN = quote_cases.json and QUOTED = merged quote outputs; each quoted form is evaluated."""
import json, os, subprocess, sys, tempfile
SHELLS = {"dash": ["/usr/bin/dash", "-c"], "bash --posix": ["/usr/bin/bash", "--posix", "-c"]}
PRE = "trap wait EXIT; f() { for a in \"$@\"; do printf '%s\\0' \"$a\" >&3; done; printf '\\1' >&3; }; set -f; f "
def run(shell, s, glob=False):
    """glob=True (quote mode): pathname expansion stays on and the directory holds files named a and decoy.txt, so an
    unquoted *, ? or [a] in a quoted form shows up as a changed argument."""
    with tempfile.TemporaryDirectory() as d, open(os.path.join(d, ".out"), "w+b") as out:
        pre = PRE
        if glob:
            for n in ("a", "decoy.txt"): open(os.path.join(d, n), "w").close()
            pre = PRE.replace("set -f; ", "")
        p = subprocess.run(["env", "-i", "PATH=/nonexistent", "HOME=/nonexistent-home", *SHELLS[shell], pre + s], cwd=d, pass_fds=(out.fileno(),),
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
                           preexec_fn=lambda: os.dup2(out.fileno(), 3))
        out.seek(0); raw = out.read()
    recs = [r.split(b"\0")[:-1] for r in raw.split(b"\1")[:-1]]
    recs = [[x.decode("utf-8", "replace") for x in r] for r in recs]
    if not recs: return dict(error=f"exit {p.returncode}: " + p.stderr.decode("utf-8", "replace").strip().splitlines()[-1][:100] if p.stderr else f"exit {p.returncode}")
    r = dict(argv=recs[0])
    if len(recs) > 1: r["more_commands"] = recs[1:]
    if p.stderr: r["stderr"] = p.stderr.decode("utf-8", "replace").strip()[:100]
    return r
mode = sys.argv[1]
cases = json.load(open(sys.argv[2]))
if mode == "split":
    out = {sh: {c["id"]: run(sh, c["s"]) for c in cases} for sh in SHELLS}
else:
    quoted = json.load(open(sys.argv[3]))
    out = {sh: {lib: {cid: (run(sh, q["argv"], glob=True) if "argv" in q else dict(error="quote failed")) for cid, q in m.items()} for lib, m in quoted.items()} for sh in SHELLS}
json.dump(out, sys.stdout, indent=1, ensure_ascii=False); print()
