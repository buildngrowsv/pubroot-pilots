"""Shared normalisation and classing. A result is {"ref": [registry, repository, tag, digest]} or {"error": ...}.
Docker's documented defaults are applied to every result alike, so libraries that leave them implicit are not
penalised: a missing registry is docker.io, index.docker.io is docker.io, a one-component Docker Hub repository gets
library/, and a reference with neither tag nor digest gets tag latest.
Classes: A same (registry, repository, tag, digest) as distribution/reference; W different; R library error where the
reference parses; L library parses a string the reference rejects."""
REF = "distribution/reference"
def norm(r):
    reg, repo, tag, dg = r["ref"]
    if reg is None or reg == "index.docker.io": reg = "docker.io"
    if reg == "docker.io" and repo is not None and "/" not in repo: repo = "library/" + repo
    if tag is None and dg is None: tag = "latest"
    return [reg, repo, tag, dg]
def klass(ref, o):
    if "error" in ref: return "A" if "error" in o else "L"
    if "error" in o: return "R"
    return "A" if norm(ref) == norm(o) else "W"
