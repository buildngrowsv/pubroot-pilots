#!/usr/bin/env python3
"""Python subjects. Usage: run.py CASES.json -> {lib: {id: {"ref": [registry, repository, tag, digest]} | {"error"}}}
- docker-image-py 0.2.0: Reference.parse_normalized_named(s), then .split_hostname() for (domain, path), ["tag"], ["digest"].
- docker (docker-py) 7.2.0: the path the SDK's images.pull() takes for a string without an explicit tag argument:
  utils.parse_repository_tag(s) -> (repository, tag-or-digest; '@' gives a digest, ':' a tag), then
  auth.resolve_repository_name(repository) -> (registry, remote name)."""
import json, sys
import docker.utils, docker.auth
import docker_image.reference as dref
def dimg(s):
    n = dref.Reference.parse_normalized_named(s)
    dom, path = n.split_hostname()
    return [dom, path, n["tag"], n["digest"]]
def dpy(s):
    repo, t = docker.utils.parse_repository_tag(s)
    tag, dg = (None, t) if "@" in s and t == s.rsplit("@", 1)[1] else (t, None)
    reg, name = docker.auth.resolve_repository_name(repo)
    return [reg, name, tag, dg]
LIBS = {"docker-image-py": dimg, "docker-py": dpy}
if __name__ == "__main__":
    cases = json.load(open(sys.argv[1])); out = {l: {} for l in LIBS}
    for c in cases:
        for l, f in LIBS.items():
            try: out[l][c["id"]] = dict(ref=f(c["s"]))
            except Exception as e: out[l][c["id"]] = dict(error=f"{type(e).__name__}: {e}"[:200])
    json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
