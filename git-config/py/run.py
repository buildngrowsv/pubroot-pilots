#!/usr/bin/env python3
"""Python subjects: dulwich ConfigFile, GitPython GitConfigParser, pygit2 Config (libgit2). Usage: run.py CASES.json
Each case is written to a file and parsed; output per library and case is {"entries": [[key, value|null], ...]} or
{"error": "..."}. Keys are section.subsection.name with section and name lower-cased by us (git treats them
case-insensitively) and the subsection as the library reports it."""
import json, os, re, sys, tempfile, io
import dulwich, dulwich.config, git, pygit2
def key(sec, sub, name): return sec.lower() + ("" if sub is None else "." + sub) + "." + name.lower()
def b2s(x): return x.decode("utf-8", "surrogateescape") if isinstance(x, bytes) else x
def dul(path, text):
    cf = dulwich.config.ConfigFile.from_path(path); out = []
    for sec in cf.sections():
        sec = [b2s(x) for x in sec]
        for name, value in cf[tuple(x.encode() for x in sec)].items():
            out.append([key(sec[0], sec[1] if len(sec) > 1 else None, b2s(name)), b2s(value)])
    return out
SUB = re.compile(r'^(\S+)\s+"(.*)"$')
def gitpython(path, text):
    cp = git.GitConfigParser(path, read_only=True); cp.read(); out = []
    for sec in cp.sections():
        m = SUB.match(sec); s, sub = (m.group(1), m.group(2)) if m else (sec, None)
        for name, values in cp.items_all(sec):
            for v in values: out.append([key(s, sub, name), v])
    return out
def pg2(path, text):
    cfg = pygit2.Config(path); return [[e.name, e.value] for e in cfg]
LIBS = {"dulwich": dul, "GitPython": gitpython, "pygit2 (libgit2)": pg2}
if __name__ == "__main__":
    cases = json.load(open(sys.argv[1])); res = {l: {} for l in LIBS}
    with tempfile.TemporaryDirectory() as d:
        for c in cases:
            for l, f in LIBS.items():
                p = os.path.join(d, f"{c['id']}-{len(res[l])}.config"); open(p, "wb").write(c["text"].encode())
                try: res[l][c["id"]] = dict(entries=f(p, c["text"]))
                except Exception as e: res[l][c["id"]] = dict(error=f"{type(e).__name__}: {str(e).replace(d, '<dir>')}"[:300])
    json.dump(res, sys.stdout, indent=1, ensure_ascii=False)
