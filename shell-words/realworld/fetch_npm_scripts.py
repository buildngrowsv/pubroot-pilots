#!/usr/bin/env python3
"""Builds the real-world sample: the "scripts" of the first 500 names in npmTopDownloads from npm-high-impact 1.13.0
(the list ships in that pinned package), read from each package's manifest on registry.npmjs.org.
First run: resolves each name's "latest" version and writes npm_scripts.json (name, version, scripts).
Later runs with --verify re-fetch the pinned name@version manifests and check the scripts are unchanged
(published npm versions are immutable). Read-only HTTP GETs; no login."""
import json, sys, subprocess, tarfile, io, urllib.request, urllib.parse, concurrent.futures as cf, re
N = 500; LIST = "https://registry.npmjs.org/npm-high-impact/-/npm-high-impact-1.13.0.tgz"
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "shell-words-pilot"}), timeout=60) as r: return r.read()
def names():
    t = tarfile.open(fileobj=io.BytesIO(get(LIST)))
    src = t.extractfile("package/lib/top-download.js").read().decode()
    return re.findall(r"^\s+'([^']+)',?$", src, re.M)[:N]
def manifest(name, ver):
    return json.loads(get("https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@") .replace("@", "@", 1).replace("/", "%2F") + "/" + ver))
if __name__ == "__main__":
    if "--verify" in sys.argv:
        snap = json.load(open("npm_scripts.json")); bad = 0
        with cf.ThreadPoolExecutor(8) as ex:
            for p, m in zip(snap["packages"], ex.map(lambda p: manifest(p["name"], p["version"]), snap["packages"])):
                if m.get("scripts", {}) != p["scripts"]: bad += 1; print("changed:", p["name"], file=sys.stderr)
        print(f"verified {len(snap['packages'])} manifests, {bad} changed"); sys.exit(1 if bad else 0)
    ns = names(); assert len(ns) == N, len(ns)
    with cf.ThreadPoolExecutor(8) as ex: ms = list(ex.map(lambda n: manifest(n, "latest"), ns))
    pk = [dict(name=n, version=m["version"], scripts=m.get("scripts", {})) for n, m in zip(ns, ms)]
    json.dump(dict(source="npm-high-impact 1.13.0 npmTopDownloads[0:500]", packages=pk), open("npm_scripts.json", "w"), indent=1, ensure_ascii=False)
    print(len(pk), "packages,", sum(len(p["scripts"]) for p in pk), "scripts")
