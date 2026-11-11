# range-parsers

Supports the Pubroot draft "Same Range Header, Different Byte Windows" (batch 6, 2026-11-11).

58 `Range` header cases (`cases.json`, written by `gen_cases.py`) are sent as identical raw HTTP/1.1 requests to seven
static-file paths running on 127.0.0.1: Express 5 `res.sendFile` (send + range-parser), `@fastify/send`, Starlette
`FileResponse` under uvicorn, aiohttp `web.FileResponse`, Werkzeug `send_file(conditional=True)`, Tornado
`StaticFileHandler` and Go `net/http.ServeContent`. `driver.py` normalises each response to status + served byte
windows; `analyze.py` builds the matrix and classes each outcome against RFC 9110 Section 14.

Reproduce (Node 24, Python 3.13, Go 1.27):

    cd js && npm ci && cd ..
    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/<impl>.json`, `results/summary.json`, `results/report.txt`, `results/versions.txt`.
The script starts its own servers in new sessions and stops only those. No network beyond 127.0.0.1, no keys. Cost: $0.
