# accept-qvalue

Supports the Pubroot draft "Same Accept Header, Different Preference Order" (batch 6, 2026-11-11).

68 `Accept` header cases, each with a fixed list of server offers (`cases.json`, written by `gen_cases.py`), are run
in-process through eight negotiators: accepts 2.0.0 (Express 5) and accepts 1.3.8 (Express 4), Werkzeug
`accept_mimetypes.best_match` (Flask), Django `HttpRequest.get_preferred_type`, Falcon `Request.client_prefers`,
and Go munnerz/goautoneg `Negotiate`, golang/gddo `httputil.NegotiateContentType` and elnormous/contenttype
`GetAcceptableMediaType`. `analyze.py` compares choices and checks them against the RFC 9110 readings in
`expected.json` (45 cases where the RFC fixes the answer).

Reproduce (Node 24, Python 3.13, Go 1.27; Go modules are pinned in go/go.mod and go/go.sum):

    cd js && npm ci && cd ..
    python3 -m venv .venv && .venv/bin/pip install -r py/requirements.txt
    PY=.venv/bin/python ./run_all.sh

Outputs: `results/node.json`, `results/py.json`, `results/go.json`, `results/summary.json`, `results/report.txt`,
`results/versions.txt`. No network at run time, no keys. Cost: $0.
