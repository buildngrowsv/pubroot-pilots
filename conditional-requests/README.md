# conditional-requests

Supports the Pubroot draft "Revalidation Under Test: How Fourteen Static-File Servers Evaluate HTTP Preconditions"
(batch 8, 2026-11-20).

54 conditional-request cases (`cases.json`, written by `gen_cases.py`) are sent as identical raw HTTP/1.1 requests to
fourteen static-file paths on 127.0.0.1, all serving the same 100-byte file whose mtime is set to
2026-01-15T12:00:00Z:

- Node: Express 5 `res.sendFile` (send), `@fastify/send`, sirv, serve-handler
- Python: Starlette `StaticFiles` under uvicorn, aiohttp static, Werkzeug `send_file`, Tornado `StaticFileHandler`,
  Falcon ASGI `add_static_route`, Django `django.views.static.serve`
- Go: `net/http.ServeContent` (with a strong ETag set by the handler) and `http.FileServer` (no ETag)
- Rust: tower-http `ServeDir` under axum, actix-files `Files`

Cases cover If-None-Match (N01-N13), If-Modified-Since (M01-M13), both together (C01-C04), If-Match (I01-I07),
If-Unmodified-Since (U01-U06) and precedence between them (P01-P09); 5 cases are marked open (no single RFC reading).
`{E}` in a header template is the ETag the server sent on a plain GET, `{EW}`/`{ES}` its weak/strong form, `{EU}` the
unquoted opaque tag and `{X}` a non-matching tag. `rfc.py` is the RFC 9110 reading (Sections 8.8.3.2, 13.1, 13.2.2);
`driver.py` records status, whether the 304 carries the ETag, body length and Content-Type; `analyze.py` builds
the matrix and classes each outcome.

Reproduce (Node 24, Python 3.13, Go 1.27, Rust 1.85):

    cd js && npm ci && cd ..
    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/<impl>.json`, `results/summary.json`, `results/report.txt`, `results/versions.txt`. The script starts
its own servers in new sessions and stops only those. No network beyond 127.0.0.1, no keys. Cost: $0.

`realworld/` holds a one-off snapshot (not part of `run_all.sh`): `probe.py` sent 21 conditional requests to each of
40 public static URLs (`urls.txt`) on 2026-11-20, twice; `rw-1.json` and `rw-2.json` keep statuses and ETag
presence only, and `analyze_rw.py` scores the If-None-Match / If-Modified-Since cases against the same reading.
Re-running `probe.py` contacts those sites and will see whatever they serve that day.
