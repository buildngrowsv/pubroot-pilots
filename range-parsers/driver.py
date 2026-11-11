#!/usr/bin/env python3
"""Send every case in cases.json as a raw HTTP/1.1 request (identical bytes for every server) and normalise the response.
Usage: driver.py NAME PORT > results/NAME.json"""
import json, os, re, socket, sys
HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = {100: ("0123456789" * 10).encode(), 0: b""}

def raw_get(port, path, rng):
    req = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nRange: {rng}\r\nConnection: close\r\n\r\n".encode("latin-1")
    s = socket.create_connection(("127.0.0.1", port), timeout=10); s.sendall(req)
    buf = b""
    while True:
        d = s.recv(65536)
        if not d: break
        buf += d
    s.close(); return buf

def parse(buf):
    head, _, body = buf.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    status = int(lines[0].split()[1]); h = {}
    for l in lines[1:]:
        k, _, v = l.partition(":"); h.setdefault(k.strip().lower(), v.strip())
    if h.get("transfer-encoding", "").lower() == "chunked":
        out = b""
        while body:
            n, _, rest = body.partition(b"\r\n"); n = int(n.split(b";")[0], 16)
            if n == 0: break
            out += rest[:n]; body = rest[n + 2:]
        body = out
    elif "content-length" in h:
        body = body[:int(h["content-length"])]
    return status, h, body

CR = re.compile(r"bytes (\d+)-(\d+)/(\d+|\*)$")
def windows_ok(cr, data, content):
    m = CR.match(cr or "")
    if not m: return None, False
    a, b = int(m.group(1)), int(m.group(2))
    return f"{a}-{b}", data == content[a:b + 1]

def normalise(status, h, body, content):
    ct = h.get("content-type", "")
    if status == 206 and "multipart/byteranges" in ct:
        bnd = re.search(r'boundary="?([^";]+)"?', ct).group(1).encode()
        wins, ok = [], True
        for part in body.split(b"--" + bnd)[1:]:
            if part.startswith(b"--"): break
            ph, _, pb = part.partition(b"\r\n\r\n")
            if pb.endswith(b"\r\n"): pb = pb[:-2]
            cr = next((l.split(b":", 1)[1].strip().decode() for l in ph.split(b"\r\n") if l.lower().startswith(b"content-range")), None)
            w, o = windows_ok(cr, pb, content); wins.append(w); ok &= o
        return f"206 multi[{','.join(map(str, wins))}]", ok
    if status == 206:
        cr = h.get("content-range")
        w, ok = windows_ok(cr, body, content)
        m = CR.match(cr or "")
        if not m or int(m.group(1)) > int(m.group(2)):
            return f"206 cr={cr}", False  # malformed or empty Content-Range
        return f"206 {w}", ok
    if status == 200:
        return ("200 full" if body == content else f"200 len={len(body)}"), body == content
    if status == 416:
        return f"416 cr={h.get('content-range', '-')}", True
    return f"{status}", True

def main():
    name, port = sys.argv[1], int(sys.argv[2])
    cases = json.load(open(os.path.join(HERE, "cases.json")))
    out = []
    for c in cases:
        try:
            st, h, body = parse(raw_get(port, f"/r{c['size']}.txt", c["range"]))
            label, ok = normalise(st, h, body, CONTENT[c["size"]])
        except Exception as e:
            label, ok = f"ERR {type(e).__name__}", False
        out.append({"id": c["id"], "outcome": label, "body_ok": ok})
    json.dump({"impl": name, "rows": out}, sys.stdout, indent=1); print()
if __name__ == "__main__": main()
