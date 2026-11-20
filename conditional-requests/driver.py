#!/usr/bin/env python3
"""Fetch /d.txt once without preconditions to learn the server's ETag and Last-Modified, then send every case in
cases.json as a raw HTTP/1.1 request (header templates filled from that ETag; see rfc.py) and record the status and
the response metadata that RFC 9110 constrains on 304. Usage: driver.py NAME PORT > results/NAME.json"""
import json, os, socket, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rfc
CONTENT = ("0123456789" * 10).encode()

def raw(port, method, headers):
    req = f"{method} /d.txt HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers) + "Connection: close\r\n\r\n"
    s = socket.create_connection(("127.0.0.1", port), timeout=10); s.sendall(req.encode("latin-1"))
    buf = b""
    while True:
        d = s.recv(65536)
        if not d: break
        buf += d
    s.close()
    head, _, body = buf.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n"); h = {}
    for l in lines[1:]:
        k, _, v = l.partition(":"); h.setdefault(k.strip().lower(), v.strip())
    return int(lines[0].split()[1]), h, body

def main():
    name, port = sys.argv[1], int(sys.argv[2])
    st, h, body = raw(port, "GET", [])
    etag, lm = h.get("etag"), h.get("last-modified")
    if etag is not None and not rfc.ETAG.match(etag): etag_note = "malformed"
    else: etag_note = "none" if etag is None else ("weak" if etag.startswith("W/") else "strong")
    base = dict(status=st, etag_kind=etag_note, last_modified=lm, body_ok=body == CONTENT, content_length=h.get("content-length"))
    rows = []
    for c in json.load(open(os.path.join(HERE, "cases.json"))):
        hs = rfc.headers_for(c, etag if etag_note in ("weak", "strong") else None)
        if hs is None: rows.append(dict(id=c["id"], status="n/a")); continue
        try:
            s, rh, b = raw(port, c["method"], hs)
            rows.append(dict(id=c["id"], status=s, etag=("same" if rh.get("etag") == etag else ("none" if "etag" not in rh else "other")),
                             # error pages (412/400) are not compared: their size depends on the install path
                             # (Express's default error page prints a stack trace)
                             body=len(b) if s in (200, 304) else None, cl=rh.get("content-length") if s in (200, 304) else None,
                             ct="content-type" in rh, lm="last-modified" in rh))
        except Exception as e:
            rows.append(dict(id=c["id"], status=f"ERR {type(e).__name__}"))
    json.dump(dict(impl=name, baseline=base, rows=rows), sys.stdout, indent=1); print()
if __name__ == "__main__": main()
