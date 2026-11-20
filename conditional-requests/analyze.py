#!/usr/bin/env python3
"""Matrix of statuses per (server, case), classed against the RFC 9110 reading (rfc.py), plus 304 metadata checks.
Classes: A agrees; M 200 where 304 (missed revalidation); F 304 where 200 (stale 'not modified'); P 200/304 where
412 (precondition ignored); X 412 where 200/304; O other status or error; - open case; n/a needs an ETag the server lacks."""
import json, os, sys, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rfc
IMPLS = ["express", "fastify_send", "sirv", "serve_handler", "starlette", "aiohttp", "werkzeug", "tornado", "falcon", "django",
         "go_servecontent", "go_fileserver", "tower_http", "actix_files"]
cases = json.load(open(os.path.join(HERE, "cases.json")))
R = {i: json.load(open(os.path.join(HERE, "results", f"{i}.json"))) for i in IMPLS}
SYN = {"weak": 'W/"o"', "strong": '"o"', "none": None, "malformed": None}
def klass(exp, got):
    if exp == "OPEN": return "-"
    if exp == "N/A" or got == "n/a": return "n/a"
    if got == exp: return "A"
    if exp == 304 and got == 200: return "M"
    if exp == 200 and got == 304: return "F"
    if exp == 412 and got in (200, 304): return "P"
    if exp in (200, 304) and got == 412: return "X"
    return "O"
rows, cc, defects = [], {i: collections.Counter() for i in IMPLS}, {i: collections.Counter() for i in IMPLS}
for c in cases:
    row = dict(id=c["id"], group=c["group"], method=c["method"], headers=c["headers"], open=c["open"], note=c["note"], exp={}, got={}, cls={})
    for i in IMPLS:
        kind = R[i]["baseline"]["etag_kind"]; exp = rfc.reading(c, SYN[kind], R[i]["baseline"]["last_modified"] is not None)
        g = next(r for r in R[i]["rows"] if r["id"] == c["id"])
        row["exp"][i] = exp; row["got"][i] = g["status"]; k = klass(exp, g["status"]); row["cls"][i] = k; cc[i][k] += 1
        if g["status"] == 304:
            defects[i]["304s"] += 1
            if kind in ("weak", "strong") and g["etag"] != "same": defects[i]["304 without the ETag"] += 1
            if g["body"]: defects[i]["304 with body bytes"] += 1
            if g["cl"] not in (None, "100"): defects[i][f"304 Content-Length {g['cl']}"] += 1
            if g["ct"]: defects[i]["304 with Content-Type"] += 1
    rows.append(row)
scored = [r for r in rows if not r["open"]]
dis = [r for r in rows if len({str(v) for v in r["got"].values() if v != "n/a"}) > 1]
dev = [r for r in scored if any(k not in ("A", "n/a") for k in r["cls"].values())]
pair = {f"{a} vs {b}": sum(1 for r in rows if "n/a" not in (r["got"][a], r["got"][b]) and r["got"][a] != r["got"][b]) for a, b in itertools.combinations(IMPLS, 2)}
summary = dict(n_cases=len(rows), n_open=sum(r["open"] for r in rows), n_status_split=len(dis), n_scored_with_deviation=len(dev),
               baseline={i: R[i]["baseline"] for i in IMPLS}, classes={i: dict(cc[i]) for i in IMPLS},
               defects_304={i: dict(defects[i]) for i in IMPLS}, pairwise=pair, rows=rows)
json.dump(summary, open(os.path.join(HERE, "results", "summary.json"), "w"), indent=1)
print(f"cases {len(rows)} (open {summary['n_open']}); status differs across servers on {len(dis)}; scored cases with a deviation: {len(dev)}")
print("baseline (ETag kind, Last-Modified, 200 body ok):")
for i in IMPLS: b = R[i]["baseline"]; print(f"  {i:<16} {b['status']} {b['etag_kind']:<7} {b['last_modified']} body_ok={b['body_ok']}")
print("classes A/M/F/P/X/O/-/n/a:")
for i in IMPLS: print(f"  {i:<16}", " ".join(f"{k}={cc[i][k]}" for k in ("A", "M", "F", "P", "X", "O", "-", "n/a")))
print("304 metadata:")
for i in IMPLS: print(f"  {i:<16}", dict(defects[i]))
print("pairwise status differences (min/max):", min(pair.values()), max(pair.values()))
for r in rows:
    print(f"{r['id']} {r['method']} {r['headers']}{' OPEN' if r['open'] else ''}")
    print("   ", " ".join(f"{i}={r['got'][i]}/{r['cls'][i]}" for i in IMPLS))
