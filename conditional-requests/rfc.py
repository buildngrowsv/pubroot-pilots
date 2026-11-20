"""RFC 9110 reading for one conditional request against a server whose selected representation has entity-tag
`etag` (string as served, or None) and Last-Modified LM. Implements sections 8.8.3.2 (comparison), 13.1.1-13.1.4
and the evaluation order of 13.2.2 for GET/HEAD. has_lm=False means the server sends no Last-Modified, so date preconditions are ignored. Returns 200, 304, 412, 'OPEN' or 'N/A' (needs an ETag the server
does not send)."""
import re, calendar, time
LM = calendar.timegm((2026, 1, 15, 12, 0, 0))
NOW = calendar.timegm((2026, 11, 20, 0, 0, 0))  # only used for the RFC 850 two-digit-year rule
ETAG = re.compile(r'(W/)?("[\x21\x23-\x7e\x80-\xff]*")$')
WD = "Mon|Tue|Wed|Thu|Fri|Sat|Sun"; WDL = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
IMF = re.compile(rf"(?:{WD}), (\d\d) ({'|'.join(MON)}) (\d{{4}}) (\d\d):(\d\d):(\d\d) GMT$")
R850 = re.compile(rf"(?:{WDL}), (\d\d)-({'|'.join(MON)})-(\d\d) (\d\d):(\d\d):(\d\d) GMT$")
ASC = re.compile(rf"(?:{WD}) ({'|'.join(MON)}) ([ \d]\d) (\d\d):(\d\d):(\d\d) (\d{{4}})$")

def http_date(v):
    """Seconds since epoch for exactly one HTTP-date (all three forms), else None."""
    v = v.strip()
    if m := IMF.match(v): d, mo, y, H, M, S = m.groups()
    elif m := R850.match(v):
        d, mo, yy, H, M, S = m.groups(); y = 2000 + int(yy)
        if y > time.gmtime(NOW).tm_year + 50: y -= 100
    elif m := ASC.match(v): mo, d, H, M, S, y = m.groups()
    else: return None
    return calendar.timegm((int(y), MON.index(mo) + 1, int(d), int(H), int(M), int(S)))

def tags(v):
    """Parse '#entity-tag' (empty elements tolerated). Returns list of (weak, opaque) or None if malformed."""
    out = []
    for el in v.split(","):  # opaque-tags in this case set never contain commas
        el = el.strip(" \t")
        if not el: continue
        m = ETAG.match(el)
        if not m: return None
        out.append((bool(m.group(1)), m.group(2)))
    return out

def fill(v, etag):
    if etag is None: return None
    m = ETAG.match(etag); opaque = m.group(2)
    return (v.replace("{EW}", "W/" + opaque).replace("{ES}", opaque).replace("{EU}", opaque.strip('"'))
             .replace("{E}", etag).replace("{X}", '"zz-nomatch"'))

def headers_for(case, etag):
    out = []
    for k, v in case["headers"]:
        if "{E" in v:
            if etag is None: return None
            v = fill(v, etag)
        else: v = v.replace("{X}", '"zz-nomatch"')
        out.append((k, v))
    return out

def reading(case, etag, has_lm=True):
    if case["open"]: return "OPEN"
    hs = headers_for(case, etag)
    if hs is None: return "N/A"
    get = {}
    for k, v in hs: get[k.lower()] = (get[k.lower()] + ", " + v) if k.lower() in get else v
    srv = ETAG.match(etag).groups() if etag else None
    srv_weak, srv_opq = (bool(srv[0]), srv[1]) if srv else (None, None)
    def strong_match(ts): return any(not w and not srv_weak and o == srv_opq for w, o in ts) if srv else False
    def weak_match(ts): return any(o == srv_opq for w, o in ts) if srv else False
    im, ius, inm, ims = (get.get(h) for h in ("if-match", "if-unmodified-since", "if-none-match", "if-modified-since"))
    if im is not None:
        if im.strip() != "*":
            ts = tags(im); assert ts is not None, case["id"]
            if not strong_match(ts): return 412
    elif ius is not None and has_lm:  # 13.1.4: ignore if the resource has no modification date
        d = http_date(ius)
        if d is not None and LM > d: return 412
    if inm is not None:
        if inm.strip() == "*": return 304
        ts = tags(inm); assert ts is not None, case["id"]
        if weak_match(ts): return 304
    elif ims is not None and has_lm:  # 13.1.3: ignore if no modification date is available
        d = http_date(ims)
        if d is not None and LM <= d: return 304
    return 200

def _fmt(t, form):
    g = time.gmtime(t); wd = time.strftime("%a", g)
    if form == "imf": return time.strftime("%a, %d %b %Y %H:%M:%S GMT", g)
    if form == "850": return time.strftime("%A, %d-%b-%y %H:%M:%S GMT", g)
    return f"{wd} {time.strftime('%b', g)} {g.tm_mday:>2} {time.strftime('%H:%M:%S %Y', g)}"

def rebase(v, site_lm):
    """Shift every HTTP-date in v (cases are written against LM) so it keeps its offset from site_lm; same form.
    Dates in 2100 (M07) and non-dates are left unchanged."""
    delta = http_date(site_lm) - LM
    def one(s):
        s = s.strip(); t = http_date(s)
        if t is None or time.gmtime(t).tm_year >= 2100: return s
        form = "imf" if IMF.match(s) else ("850" if R850.match(s) else "asc")
        return _fmt(t + delta, form)
    parts = re.findall(rf"(?:{WD}), \d\d (?:{'|'.join(MON)}) \d{{4}} \d\d:\d\d:\d\d GMT", v)
    if len(parts) > 1: return ", ".join(one(p) for p in parts)
    return one(v)
