# Pilot: default retry and idempotency behaviour of GenAI Python SDKs (G13-B)

Run on 2026-10-25 (America/Chicago) on one Linux x86_64 machine, Python 3.13. Cost was $0. Every request went to a local stub on 127.0.0.1, with fake keys. No provider API was contacted.

- `src/stub_server.py`: a failure-injecting stub that logs every attempt (`results/attempts.jsonl`). Scenarios:
  - `e500`: HTTP 500.
  - `timeout`: reads the request, then waits 2.5 s, while the client timeout is 1 s.
  - `drop`: reads the request, then closes the socket.
- `src/call_sdk.py`: makes one logical generation call per SDK with default retry settings. Only the per-attempt timeout is lowered (1 s).
- `run_matrix.sh`: 9 SDKs × 3 scenarios × 3 reps. `run_genai.sh` re-runs google-genai after a harness fix (v1 rows are kept in `results/invalid_google_genai_harness_v1.jsonl`, not used). `run_caller_key.sh` is the mitigation run, where the caller supplies an `Idempotency-Key` through `extra_headers`.
- `src/analyze.py` produces `results/summary.md` and `results/joined.json`. Mitigation results are in `results/summary_callerkey.md`. Package versions: `requirements.txt` (direct pins) and `requirements.lock.txt` (the full `pip freeze` of the original environment).

Headline (from `results/summary.md`):
- 81 logical calls produced 138 duplicate POSTs at the stub. 48 of the 81 calls made more than 1 attempt.
- 0 attempts carried an idempotency header by default.
- openai 3.37.0, anthropic 2.3.0, groq 1.7.0 and together 3.0.0 made 3 attempts in every scenario.
- cohere 7.3.0 made 3 attempts on e500 and drop, and 1 on timeout.
- fal-client 1.0.3 made 10 attempts on timeout and drop, and 1 on e500.
- mistralai 3.5.0, google-genai 2.33.0 and replicate 1.0.7 made 1 attempt in every scenario.
- A caller-supplied key was re-sent unchanged on all 3 attempts in all 12 mitigation runs.

Limits:
- This measures client behaviour only. Whether a real provider deduplicates or bills a retried generation was NOT tested.
- The replicate client's timeout argument did not take effect in this harness, so its `timeout` scenario received a delayed 500.
- Only Python SDKs at one version each were tested.

## Install and run (no keys, no provider contacted)

```bash
cd sdk-retry
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt    # or -r requirements.lock.txt for the exact original env
./run_matrix.sh                      # 81 runs -> results/attempts.jsonl, results/client.jsonl (fal-client timeout/drop runs take ~1 min each)
./run_genai.sh                       # google-genai re-run (appends)
./run_caller_key.sh                  # mitigation run -> results/client_callerkey.jsonl
.venv/bin/python src/analyze.py      # -> results/summary.md, results/joined.json
```

The run scripts delete and regenerate the committed `results/attempts.jsonl` and `results/client.jsonl`. Those files are the outputs of the original run.

## Localhost TLS certificate (generated at run time, never committed)

fal-client always connects over https, so the stub also serves TLS on 127.0.0.1:8766. **No certificate or key is included in this repository.**

Each run script calls `./gen_localhost_cert.sh`, which uses `openssl` to create a throwaway self-signed certificate for `localhost` / `127.0.0.1`, valid for 1 day. The certificate and key are written to `.certs/`, which is git-ignored. The script then passes the certificate to the client through `SSL_CERT_FILE`. `src/stub_server.py` reads it from `$STUB_CERT_DIR` (default `.certs`), and only starts the TLS port if the certificate exists. Delete `.certs/` afterwards.

The original run used a certificate generated the same way, stored under `src/` and not published. That location is the only change from the code as run. Re-running with the published code reproduces the attempt counts: openai e500 gives 3 attempts and fal-client e500 gives 1, checked on 2026-10-25.

## Files

- `src/stub_server.py`, `src/call_sdk.py`, `src/analyze.py`
- `run_*.sh`, `gen_localhost_cert.sh`
- `requirements*.txt`
- `results/`:
  - Raw attempts and client outcomes, joined table, summaries.
  - `invalid_google_genai_harness_v1.jsonl`: rows from a harness bug, kept for transparency and excluded from all counts.
