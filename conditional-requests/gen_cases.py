#!/usr/bin/env python3
"""Writes cases.json: conditional GET/HEAD requests for one 100-byte static file whose mtime run_all.sh pins to
2026-01-15T12:00:00Z (Last-Modified: Thu, 15 Jan 2026 12:00:00 GMT).
Header values are templates filled per server from its own 200 response (driver.py):
  {E}  the ETag exactly as served          {ES} its opaque-tag alone (strong form)
  {EW} W/ + its opaque-tag (weak form)     {EU} its opaque-tag without the double quotes (malformed)
  {X}  "zz-nomatch" (a tag no server issues)
The reading is computed by rfc.py (RFC 9110 sections 8.8.3, 13.1, 13.2.2) from the server's ETag kind; cases whose
outcome RFC 9110 does not fix are marked open=True and are reported, not scored."""
import json
LM, LM_P1H, LM_M1S, LM_M1D = ("Thu, 15 Jan 2026 12:00:00 GMT", "Thu, 15 Jan 2026 13:00:00 GMT",
                              "Thu, 15 Jan 2026 11:59:59 GMT", "Wed, 14 Jan 2026 12:00:00 GMT")
G, H = "GET", "HEAD"
C = [  # id, group, method, [(header, value)], open, note
 ("B01", "baseline", G, [], False, "no precondition"),
 ("B02", "baseline", H, [], False, "HEAD, no precondition"),
 ("N01", "if-none-match", G, [("If-None-Match", "{E}")], False, "exact tag"),
 ("N02", "if-none-match", G, [("If-None-Match", "{EW}")], False, "weak form of the tag"),
 ("N03", "if-none-match", G, [("If-None-Match", "{ES}")], False, "strong form of the tag"),
 ("N04", "if-none-match", G, [("If-None-Match", "{X}")], False, "other tag"),
 ("N05", "if-none-match", G, [("If-None-Match", "{X}, {E}")], False, "list, match second"),
 ("N06", "if-none-match", G, [("If-None-Match", "{X},{E}")], False, "list without space"),
 ("N07", "if-none-match", G, [("If-None-Match", "*")], False, "star"),
 ("N08", "if-none-match", G, [("If-None-Match", "{E}  ")], False, "trailing spaces (OWS)"),
 ("N09", "if-none-match", G, [("If-None-Match", "{EU}")], True, "unquoted (malformed)"),
 ("N10", "if-none-match", G, [("If-None-Match", "{X}"), ("If-None-Match", "{E}")], False, "two field lines"),
 ("N11", "if-none-match", H, [("If-None-Match", "{E}")], False, "HEAD, exact tag"),
 ("N12", "if-none-match", G, [("If-None-Match", "*, {X}")], True, "star inside a list (invalid)"),
 ("N13", "if-none-match", G, [("If-None-Match", "{EW}, {X}")], False, "list, weak form first"),
 ("M01", "if-modified-since", G, [("If-Modified-Since", LM)], False, "= Last-Modified"),
 ("M02", "if-modified-since", G, [("If-Modified-Since", LM_P1H)], False, "LM + 1 h"),
 ("M03", "if-modified-since", G, [("If-Modified-Since", LM_M1S)], False, "LM - 1 s"),
 ("M04", "if-modified-since", G, [("If-Modified-Since", "Thursday, 15-Jan-26 12:00:00 GMT")], False, "= LM, RFC 850 form"),
 ("M05", "if-modified-since", G, [("If-Modified-Since", "Thu Jan 15 12:00:00 2026")], False, "= LM, asctime form"),
 ("M06", "if-modified-since", G, [("If-Modified-Since", "yesterday")], False, "not a date"),
 ("M07", "if-modified-since", G, [("If-Modified-Since", "Fri, 01 Jan 2100 00:00:00 GMT")], False, "future date (RFC 2616 called it invalid; RFC 9110 does not)"),
 ("M08", "if-modified-since", G, [("If-Modified-Since", "Thu, 15 Jan 2026 12:00:00 UTC")], True, "UTC instead of GMT"),
 ("M09", "if-modified-since", G, [("If-Modified-Since", "Thu, 01 Jan 1970 00:00:00 GMT")], False, "epoch"),
 ("M10", "if-modified-since", H, [("If-Modified-Since", LM_P1H)], False, "HEAD, LM + 1 h"),
 ("M11", "if-modified-since", G, [("If-Modified-Since", LM + ", " + LM)], False, "two dates (more than one member)"),
 ("M12", "if-modified-since", G, [("If-Modified-Since", "thu, 15 jan 2026 12:00:00 gmt")], True, "lower case"),
 ("M13", "if-modified-since", G, [("If-Modified-Since", "Thu, 15 Jan 2026 12:00:00 GMT junk")], True, "trailing garbage"),
 ("C01", "inm+ims", G, [("If-None-Match", "{X}"), ("If-Modified-Since", LM_P1H)], False, "INM false-match + IMS unmodified"),
 ("C02", "inm+ims", G, [("If-None-Match", "{E}"), ("If-Modified-Since", LM_M1S)], False, "INM match + IMS modified"),
 ("C03", "inm+ims", G, [("If-None-Match", "{X}"), ("If-Modified-Since", "yesterday")], False, "INM other + IMS invalid"),
 ("C04", "inm+ims", G, [("If-None-Match", "*"), ("If-Modified-Since", LM_M1S)], False, "INM star + IMS modified"),
 ("I01", "if-match", G, [("If-Match", "{E}")], False, "exact tag (strong comparison)"),
 ("I02", "if-match", G, [("If-Match", "{ES}")], False, "strong form"),
 ("I03", "if-match", G, [("If-Match", "{EW}")], False, "weak form"),
 ("I04", "if-match", G, [("If-Match", "{X}")], False, "other tag"),
 ("I05", "if-match", G, [("If-Match", "*")], False, "star"),
 ("I06", "if-match", G, [("If-Match", "{X}, {ES}")], False, "list, strong form second"),
 ("I07", "if-match", H, [("If-Match", "{X}")], False, "HEAD, other tag"),
 ("U01", "if-unmodified-since", G, [("If-Unmodified-Since", LM)], False, "= LM"),
 ("U02", "if-unmodified-since", G, [("If-Unmodified-Since", LM_P1H)], False, "LM + 1 h"),
 ("U03", "if-unmodified-since", G, [("If-Unmodified-Since", LM_M1S)], False, "LM - 1 s"),
 ("U04", "if-unmodified-since", G, [("If-Unmodified-Since", "yesterday")], False, "not a date"),
 ("U05", "if-unmodified-since", G, [("If-Unmodified-Since", "Wednesday, 14-Jan-26 12:00:00 GMT")], False, "LM - 1 day, RFC 850"),
 ("U06", "if-unmodified-since", G, [("If-Unmodified-Since", "Thu Jan 15 12:00:00 2026")], False, "= LM, asctime"),
 ("P01", "precedence", G, [("If-Match", "*"), ("If-Unmodified-Since", LM_M1S)], False, "IM true; IUS must be ignored"),
 ("P02", "precedence", G, [("If-Match", "{X}"), ("If-Unmodified-Since", LM_P1H)], False, "IM false wins"),
 ("P03", "precedence", G, [("If-Match", "{ES}"), ("If-None-Match", "{E}")], False, "IM (strong) then INM"),
 ("P04", "precedence", G, [("If-Unmodified-Since", LM_M1S), ("If-None-Match", "{E}")], False, "IUS false before INM"),
 ("P05", "precedence", G, [("If-Unmodified-Since", LM_P1H), ("If-None-Match", "{E}")], False, "IUS true, INM match"),
 ("P06", "precedence", G, [("If-Match", "*"), ("If-None-Match", "*")], False, "IM star, INM star"),
 ("P07", "precedence", G, [("If-Unmodified-Since", LM_M1S), ("If-Modified-Since", LM_P1H)], False, "IUS false, IMS unmodified"),
 ("P08", "precedence", G, [("If-Match", "{X}"), ("If-Modified-Since", LM_P1H)], False, "IM false, IMS unmodified"),
 ("P09", "precedence", G, [("If-Match", "{X}"), ("If-None-Match", "{E}")], False, "IM false, INM match"),
]
out = [dict(id=i, group=g, method=m, headers=h, open=o, note=n) for i, g, m, h, o, n in C]
assert len({c["id"] for c in out}) == len(out)
if __name__ == "__main__":
    json.dump(out, open("cases.json", "w"), indent=1); print(len(out), "cases")
