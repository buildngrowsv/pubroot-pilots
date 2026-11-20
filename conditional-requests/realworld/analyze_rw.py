#!/usr/bin/env python3
"""Score realworld/rw.json against rfc.reading. Only If-None-Match / If-Modified-Since cases are scored (RFC 9110
13.2.2 steps 3-4 apply to caches and origins alike); If-Match / If-Unmodified-Since are origin-only (steps 1-2), and
we cannot tell whether a CDN edge answered as cache or origin, so they are reported but not scored.
Classes: A agree; M 200 where 304 read; F 304 where 200 read; X 412 on a scored case; O other; - n/a."""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import rfc
CASES = {c["id"]: c for c in json.load(open(os.path.join(HERE, "..", "cases.json")))}
d = json.load(open(os.path.join(HERE, "rw-1.json"))); d2 = json.load(open(os.path.join(HERE, "rw-2.json")))
def statuses(dd): return {(s["url"], c): (v if v == "n/a" else v["status"]) for s in dd["sites"] for c, v in s.get("rows", {}).items()}
S1, S2 = statuses(d), statuses(d2)
pass_diff = sorted(f"{u} {c}: {S1.get((u, c))} vs {S2.get((u, c))}" for u, c in set(S1) | set(S2) if S1.get((u, c)) != S2.get((u, c)))
SCORED = [c for c in d["cases"] if c[0] in "NMC"]; INFO = [c for c in d["cases"] if c[0] in "IU"]
def cls(exp, got):
    if exp == "N/A" or got == "n/a": return "-"
    if not isinstance(got, int): return "O"
    if got == exp: return "A"
    if exp == 304 and got == 200: return "M"
    if exp == 200 and got == 304: return "F"
    if got == 412: return "X"
    return "O"
sites, lines, per_case = [], [], collections.defaultdict(collections.Counter)
unstable = set()
for dd in (d, d2):
    for s in dd["sites"]:
        b = s.get("rows", {}).get("B01")
        if isinstance(b, dict) and b.get("etag") == "other": unstable.add(s["url"])
unstable |= {x.split()[0] for x in pass_diff}
for s in d["sites"]:
    if s.get("status") != 200 or s["url"] in unstable: continue
    etag = None
    rows = s["rows"]
    # recover the served tag kind only; the tag value itself is not stored. reading() needs a tag: a valid weak or
    # strong placeholder of the same kind gives the same verdict for every case here, since probes copy the served tag.
    if s["etag_kind"] == "weak": etag = 'W/"t"'
    elif s["etag_kind"] == "strong": etag = '"t"'
    has_lm = bool(s["last_modified"]) and rfc.http_date(s["last_modified"]) is not None
    row = {}
    for cid in SCORED + INFO:
        got = rows[cid]; st = got if got == "n/a" else got["status"]
        exp = rfc.reading(CASES[cid], etag, has_lm)
        row[cid] = dict(exp=exp, got=st, cls=cls(exp, st) if cid in SCORED else "info")
        if cid in SCORED: per_case[cid][row[cid]["cls"]] += 1
    tag_changed = sum(1 for c in SCORED + INFO if isinstance(rows[c], dict) and rows[c].get("etag") == "other")
    no_tag_304 = sum(1 for c in SCORED if isinstance(rows[c], dict) and rows[c]["status"] == 304 and rows[c].get("etag") == "none" and etag)
    from urllib.parse import urlsplit
    host = urlsplit(s["url"]).netloc
    cnt = collections.Counter(v["cls"] for k, v in row.items() if k in SCORED)
    sites.append(dict(host=host, server=s["server"], infra=s["infra"], etag_kind=s["etag_kind"], has_lm=has_lm,
                      counts=dict(cnt), etag_changed_in=tag_changed, n_304_without_etag=no_tag_304, rows=row))
summ = dict(fetched=[d["fetched"], d2["fetched"]], pass_differences=pass_diff, n_urls=len(d["sites"]), n_scored_sites=len(sites),
            unstable_excluded=sorted(unstable), excluded=[dict(url=s["url"], status=s.get("status"), error=s.get("error")) for s in d["sites"] if s.get("status") != 200],
            per_case={k: dict(v) for k, v in per_case.items()}, sites=sites)
json.dump(summ, open(os.path.join(HERE, "rw_summary.json"), "w"), indent=1)
L = [f"pass 1 {d['fetched']}, pass 2 {d2['fetched']}; status differences between passes: {len(pass_diff)}", *["  " + x for x in pass_diff], f"{len(d['sites'])} URLs; {len(sites)} answered 200 and are scored", "",
     "host | server | etag | LM | " + " ".join(SCORED) + " | info " + " ".join(INFO)]
for s in sites:
    L.append(f"{s['host']} | {s['server']} | {s['etag_kind']} | {'y' if s['has_lm'] else 'n'} | " +
             " ".join(s['rows'][c]['cls'] for c in SCORED) + " | " + " ".join(str(s['rows'][c]['got']) for c in INFO) +
             (f" | other ETag in {s['etag_changed_in']}" if s['etag_changed_in'] else "") + (f" | 304 w/o ETag {s['n_304_without_etag']}" if s['n_304_without_etag'] else ""))
L += ["", "per case: " + "; ".join(f"{c} " + ",".join(f"{k}{v}" for k, v in sorted(per_case[c].items())) for c in SCORED)]
dev = [s for s in sites if any(k in s["counts"] for k in "MFXO")]
L.append(f"sites with >=1 deviation on scored cases: {len(dev)}/{len(sites)}")
for skip in (("M07",), ("M07", "M11"), ("M07", "M11", "N10")):
    n = sum(1 for s in sites if any(v["cls"] in "MFXO" for c, v in s["rows"].items() if c in SCORED and c not in skip))
    L.append(f"  ... ignoring {'/'.join(skip)}: {n}/{len(sites)}")
c04 = [s["host"] for s in sites if s["rows"]["C04"]["cls"] == "M"]
L.append(f"C04 (INM * + IMS older than LM) answered 200: {len(c04)} {c04}")
L.append("N10 400 responses: " + str([s["host"] for s in sites if s["rows"]["N10"]["got"] == 400]))
L.append("304 carrying a different ETag than sent: " + str([s["host"] for s in sites if s["etag_changed_in"]]))
open(os.path.join(HERE, "rw_report.txt"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
