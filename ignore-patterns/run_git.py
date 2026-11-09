#!/usr/bin/env python3
import json, os, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(HERE, "cases", "meta.json")))
results = {}
for name in meta["pattern_names"]:
    body = open(os.path.join(HERE, "cases", f"{name}.ignore")).read()
    td = tempfile.mkdtemp(prefix="igin-")
    try:
        subprocess.check_call(["git", "init", "-q"], cwd=td)
        open(os.path.join(td, ".gitignore"), "w").write(body)
        # create placeholder files so check-ignore can see dirs? check-ignore --no-index works on paths without files
        paths = [p for p, _ in meta["paths"]]
        # git check-ignore --stdin -z --no-index
        proc = subprocess.run(
            ["git", "check-ignore", "--stdin", "--no-index", "-v"],
            input="\n".join(paths) + "\n",
            text=True, capture_output=True, cwd=td,
        )
        ignored = set()
        for line in proc.stdout.splitlines():
            # format: <source> <LINENUM>:<pattern> <path>
            # last field is path
            parts = line.split("\t") if "\t" in line else line.rsplit(" ", 1)
            if len(parts) >= 2:
                ignored.add(parts[-1])
            else:
                # fallback: last token
                ignored.add(line.split()[-1])
        results[name] = {p: (p in ignored) for p, _ in meta["paths"]}
    finally:
        shutil.rmtree(td, ignore_errors=True)
json.dump(results, open(os.path.join(HERE, "results", "git.json"), "w"), indent=2, sort_keys=True)
print("git cases", len(results))
