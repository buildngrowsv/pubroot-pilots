#!/usr/bin/env python3
"""Builds the real-world sample: every `image:` value in the YAML files of six public repositories of compose files,
Kubernetes manifests, Argo workflows and Tekton tasks (SOURCES) at pinned commits (shallow fetch of exactly those commits, read-only). Values with template syntax
(${...}, {{...}}, $VAR) are skipped and counted. Writes image_refs.json: source, commit, file, line, ref."""
import json, os, re, subprocess, tempfile, sys
SOURCES = [("docker/awesome-compose", "503c0dcef31b07fb77b2d4c5556bfafdf86f4f1a"),
           ("kubernetes/examples", "22934a040acbb0c0aa103023ccbd871507bf17f6"),
           ("argoproj/argo-workflows", "c2b35edf4829b1fcbc5cebafd77b8cebc8eb9709"),
           ("GoogleCloudPlatform/kubernetes-engine-samples", "2c7091f9066e82d036e16f0a0ab68a18b09d29e1"),
           ("GoogleCloudPlatform/microservices-demo", "c7cb6d5bfd6ea3aed768634ebbcb98cb7a523712"),
           ("tektoncd/catalog", "112374ce1262b133a77300bd8133445722605e04")]
IMG = re.compile(r"""^\s*-?\s*image:\s*(?P<v>"[^"]*"|'[^']*'|[^\s#]+)""")
def git(*a, cwd=None): subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, env={"PATH": "/usr/bin:/bin", "GIT_TERMINAL_PROMPT": "0", "HOME": "/nonexistent"})
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    refs, skipped = [], 0
    with tempfile.TemporaryDirectory() as d:
        for repo, sha in SOURCES:
            w = os.path.join(d, repo.replace("/", "_")); os.makedirs(w)
            git("init", "-q", cwd=w); git("fetch", "-q", "--depth", "1", f"https://github.com/{repo}", sha, cwd=w); git("checkout", "-q", "FETCH_HEAD", cwd=w)
            for root, _, files in sorted(os.walk(w)):
                if "/.git" in root: continue
                for f in sorted(files):
                    if not f.endswith((".yml", ".yaml")): continue
                    p = os.path.join(root, f); rel = os.path.relpath(p, w)
                    for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                        m = IMG.match(line)
                        if not m: continue
                        v = m.group("v").strip("'\"")
                        if not v or "$" in v or "{{" in v: skipped += 1; continue
                        refs.append(dict(source=repo, commit=sha, file=rel, line=i, ref=v))
    json.dump(dict(sources=SOURCES, skipped_templated=skipped, refs=refs), open("image_refs.json", "w"), indent=1)
    print(len(refs), "references,", len({r["ref"] for r in refs}), "distinct;", skipped, "templated skipped")
