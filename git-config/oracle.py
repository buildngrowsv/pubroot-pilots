#!/usr/bin/env python3
"""Reference: git itself. Each case is written to a file in a fresh directory and read with
`git config -f FILE --list -z` (no includes are followed with -f) in an empty environment with no global or system
config. Output: per case either {"entries": [[key, value-or-null], ...]} in file order, or {"error": message}."""
import json, os, subprocess, sys, tempfile
def run(text):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "config")
        open(f, "wb").write(text.encode())
        env = {"PATH": os.environ["PATH"], "HOME": d, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "LC_ALL": "C"}
        p = subprocess.run(["git", "config", "-f", f, "--list", "-z"], capture_output=True, env=env, cwd=d)
        if p.returncode: return dict(error=p.stderr.decode(errors="replace").strip().replace(d, "<dir>"))
        ents = []
        for rec in p.stdout.split(b"\0")[:-1]:
            k, nl, v = rec.partition(b"\n")
            ents.append([k.decode(), v.decode() if nl else None])
        return dict(entries=ents)
if __name__ == "__main__":
    cases = json.load(open(sys.argv[1]))
    json.dump({c["id"]: run(c["text"]) for c in cases}, sys.stdout, indent=1, ensure_ascii=False)
