#!/usr/bin/env python3
"""Builds the real-world sample: git config files from (a) the 100 most-starred GitHub repositories named "dotfiles"
(GitHub repository search `dotfiles in:name`, sorted by stars, read once on the snapshot date) and (b) the repositories
linked under "Example dotfiles repos" in webpro/awesome-dotfiles at commit a6bf526494f0923adc30f9d4bf631019091155f6.
The repository list is stored in gitconfigs.json, so later runs do not depend on search results. For each repository, the commit of its
default branch is resolved with `git ls-remote` and the first existing file among PATHS is read from
raw.githubusercontent.com at that commit.
Writes gitconfigs.list.json (repo, commit, path, sha256; committed) and snapshot.local.json (the file texts; not
committed, because personal config files carry their owners' names and e-mail addresses).
--restore rebuilds snapshot.local.json from the committed list and checks every sha256. Read-only, unauthenticated."""
import hashlib
import json, re, subprocess, sys, urllib.request
LIST = "https://raw.githubusercontent.com/webpro/awesome-dotfiles/a6bf526494f0923adc30f9d4bf631019091155f6/README.md"
PATHS = [".gitconfig", "gitconfig", "git/gitconfig", "git/config", ".config/git/config", "git/.gitconfig", "gitconfig.symlink",
         "git/gitconfig.symlink", "home/.gitconfig", "dot_gitconfig", "config/git/config"]
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "git-config-pilot"}), timeout=30) as r: return r.read()
    except Exception: return None
def repos():
    md = get(LIST).decode(); sec = md.split("## Example dotfiles repos")[1].split("\n## ")[0]
    refs = dict(re.findall(r"^\[([^\]]+)\]:\s*(\S+)", md, re.M))   # reference-style link definitions
    urls = [refs.get(k, "") for k in re.findall(r"\]\[([^\]]+)\]", sec)] + re.findall(r"\((https://github\.com/[^)\s]+)\)", sec)
    out = []
    for u in urls:
        m = re.match(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", u)
        if m and m.groups() not in out: out.append(m.groups())
    return out
def top_dotfiles():
    d = json.loads(get("https://api.github.com/search/repositories?q=dotfiles+in:name&sort=stars&order=desc&per_page=100"))
    return [tuple(i["full_name"].split("/")) for i in d["items"]]
if __name__ == "__main__":
    import os; os.chdir(os.path.dirname(os.path.abspath(__file__)))   # files live next to this script
    if "--restore" in sys.argv:
        s = json.load(open("gitconfigs.list.json")); bad = 0; files = []
        for f in s["files"]:
            b = get(f"https://raw.githubusercontent.com/{f['repo']}/{f['commit']}/{f['path']}")
            if b is None or hashlib.sha256(b).hexdigest() != f["sha256"]: bad += 1; print("changed:", f["repo"], file=sys.stderr); continue
            files.append(dict(f, text=b.decode("utf-8", "replace")))
        json.dump(dict(s, files=files), open("snapshot.local.json", "w"), indent=1, ensure_ascii=False)
        print(f"restored {len(files)} files, {bad} changed or missing"); sys.exit(1 if bad else 0)
    files, missing = [], []
    rl = top_dotfiles(); rl += [x for x in repos() if x not in rl]
    for o, r in rl:
        p = subprocess.run(["git", "ls-remote", f"https://github.com/{o}/{r}", "HEAD"], capture_output=True, text=True, timeout=60,
                           env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin"})
        if p.returncode or not p.stdout: missing.append(f"{o}/{r} (no HEAD)"); continue
        sha = p.stdout.split()[0]
        for path in PATHS:
            b = get(f"https://raw.githubusercontent.com/{o}/{r}/{sha}/{path}")
            if b is not None and b.strip(): files.append(dict(repo=f"{o}/{r}", commit=sha, path=path, sha256=hashlib.sha256(b).hexdigest(), text=b.decode("utf-8", "replace"))); break
        else: missing.append(f"{o}/{r} (no config file at the listed paths)")
    meta = dict(source=LIST, repositories=[f"{o}/{r}" for o, r in rl], paths=PATHS, not_found=missing)
    json.dump(dict(meta, files=files), open("snapshot.local.json", "w"), indent=1, ensure_ascii=False)
    json.dump(dict(meta, files=[{k: v for k, v in f.items() if k != "text"} for f in files]), open("gitconfigs.list.json", "w"), indent=1)
    print(len(files), "files;", len(missing), "repositories without one")
