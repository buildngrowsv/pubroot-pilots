#!/usr/bin/env python3
"""One-off snapshot (run 2026-11-20, NOT part of run_all.sh): for each public static URL in urls.txt, one plain GET to
learn ETag/Last-Modified, then the conditional cases in RW_CASES (headers filled exactly as for the local servers),
0.3 s apart. Stores statuses and a few response-header facts only (no bodies, no cookies) in rw.json.
Usage: python3 realworld/probe.py > realworld/rw-<pass>.json"""
import json, os, sys, time, http.client, ssl, datetime
from urllib.parse import urlsplit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import rfc
RW_CASES = ["B01", "N01", "N02", "N03", "N05", "N06", "N07", "N10", "N13", "M01", "M03", "M04", "M05", "M07", "M11", "C01", "C04",
            "I01", "I03", "I04", "U03"]
UA = "pubroot-pilots conditional-requests probe (one-off measurement; 21 requests per URL)"
CASES = {c["id"]: c for c in json.load(open(os.path.join(HERE, "..", "cases.json")))}
INFRA = ["cf-ray", "x-amz-cf-id", "x-served-by", "x-fastly-request-id", "x-vercel-id", "x-nf-request-id", "x-azure-ref",
         "x-akamai-transformed", "akamai-grn", "x-github-request-id", "x-goog-generation", "x-cache", "via", "age"]
def req(url, headers):
    u = urlsplit(url); c = http.client.HTTPSConnection(u.netloc, timeout=20, context=ssl.create_default_context())
    c.putrequest("GET", u.path + (("?" + u.query) if u.query else ""), skip_accept_encoding=True)
    c.putheader("User-Agent", UA); c.putheader("Accept-Encoding", "identity")
    for k, v in headers: c.putheader(k, v)
    c.endheaders(); r = c.getresponse(); r.read(); h = {k.lower(): v for k, v in r.getheaders()}; c.close()
    return r.status, h
out = dict(fetched=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), user_agent=UA, cases=RW_CASES, sites=[])
for url in [l.strip() for l in open(os.path.join(HERE, "urls.txt")) if l.strip()]:
    rec = dict(url=url)
    try:
        st, h = req(url, [])
    except Exception as e:
        rec["error"] = type(e).__name__; out["sites"].append(rec); continue
    etag, lm = h.get("etag"), h.get("last-modified")
    kind = "none" if etag is None else ("malformed" if not rfc.ETAG.match(etag) else ("weak" if etag.startswith("W/") else "strong"))
    rec.update(status=st, server=h.get("server"), infra=sorted(k for k in INFRA if k in h), etag_kind=kind,
               last_modified=lm, rows={})
    if st != 200: out["sites"].append(rec); continue
    for cid in RW_CASES:
        time.sleep(0.3)
        hs = rfc.headers_for(CASES[cid], etag if kind in ("weak", "strong") else None)
        if hs is None: rec["rows"][cid] = "n/a"; continue
        # dates in the case set are relative to the local fixture's Last-Modified; rewrite them for this resource
        if any(k.endswith("Since") for k, _ in hs):
            if lm is None or rfc.http_date(lm) is None: rec["rows"][cid] = "n/a"; continue
            hs = [(k, rfc.rebase(v, lm) if k.endswith("Since") else v) for k, v in hs]
        try:
            s, rh = req(url, hs)
            rec["rows"][cid] = dict(status=s, etag=("none" if "etag" not in rh else ("same" if rh["etag"] == etag else "other")))
        except Exception as e:
            rec["rows"][cid] = dict(status=f"ERR {type(e).__name__}")
    out["sites"].append(rec); print(url, st, kind, file=sys.stderr)
json.dump(out, sys.stdout, indent=1); print()
