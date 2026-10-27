#!/usr/bin/env python3
"""Local stub "provider" for the SDK retry audit. Never contacts any real API.

URL layout: /<run_id>/<scenario>/<anything the SDK appends>
Scenarios (applied to every request, every attempt):
  e500    -> HTTP 500 with a JSON error body
  timeout -> read the full request, then sleep SLEEP_S before answering 500 (client timeout is shorter)
  drop    -> read the full request, then close the socket without any response
Every attempt is appended to results/attempts.jsonl: run_id, scenario, method, path, time,
all headers whose name contains "idempot", x-stainless-retry-count, sha256 of the body.
"""
import hashlib, json, os, socket, ssl, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SLEEP_S = float(os.environ.get("STUB_SLEEP_S", "2.5"))
LOG = os.environ.get("STUB_LOG", "results/attempts.jsonl")
lock = threading.Lock()

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _handle(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        parts = self.path.lstrip("/").split("/")
        run_id, scen = (parts + ["", ""])[:2]
        rec = dict(t=round(time.time(), 3), run_id=run_id, scenario=scen, method=self.command, path=self.path,
                   idem_headers={k: v for k, v in self.headers.items() if "idempot" in k.lower()},
                   retry_count_header=self.headers.get("x-stainless-retry-count"),
                   body_sha256=hashlib.sha256(body).hexdigest()[:16], body_len=len(body))
        with lock, open(LOG, "a") as f: f.write(json.dumps(rec) + "\n")
        if scen == "drop":
            try: self.connection.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            self.close_connection = True; return
        if scen == "timeout": time.sleep(SLEEP_S)
        out = json.dumps({"error": {"message": "stub server error", "type": "server_error"}}).encode()
        try:
            self.send_response(500); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out))); self.send_header("Connection", "close"); self.end_headers()
            self.wfile.write(out)
        except (BrokenPipeError, ConnectionResetError): pass
        self.close_connection = True
    do_POST = do_GET = do_PUT = do_PATCH = do_DELETE = _handle

def serve(port, cert=None):
    s = ThreadingHTTPServer(("127.0.0.1", port), H); s.daemon_threads = True
    if cert:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert[0], cert[1])
        s.socket = ctx.wrap_socket(s.socket, server_side=True)
    s.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=serve, args=(8765,), daemon=True).start()
    cert_dir = os.environ.get("STUB_CERT_DIR", ".certs")   # created at run time by gen_localhost_cert.sh; never committed
    if os.path.exists(os.path.join(cert_dir, "cert.pem")):
        threading.Thread(target=serve, args=(8766, (os.path.join(cert_dir, "cert.pem"), os.path.join(cert_dir, "key.pem"))), daemon=True).start()
    print("stub up", flush=True)
    while True: time.sleep(3600)
