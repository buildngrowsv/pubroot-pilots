"""Shared classing. A config result is {"entries": [[key, value|null], ...]} or {"error": ...}. Entries are compared as
a map from key to the ordered list of its values (order across different keys is ignored).
Classes: A same map as git; T same map once git's implicit true (a name with no '=') is read as the string "true";
W different map; R library error where git parses the file; L library parses a file git rejects."""
import json
def norm(r, implicit=None):
    d = {}
    for k, v in r["entries"]: d.setdefault(k, []).append(implicit if v is None and implicit is not None else v)
    return d
def klass(ref, o):
    if "error" in ref: return "A" if "error" in o else "L"
    if "error" in o: return "R"
    if norm(ref) == norm(o): return "A"
    if norm(ref, "true") == norm(o, "true") and None not in [v for _, v in o["entries"]]: return "T"
    return "W"
def diff_keys(ref, o):
    """keys whose value lists differ (for W), as sorted list"""
    a, b = norm(ref), norm(o); return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
