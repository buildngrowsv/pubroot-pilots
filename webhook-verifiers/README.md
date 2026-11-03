# webhook-verifiers: a differential test of webhook signature verifiers

Pilot for the Pubroot submission *Same Signature, Different Verdicts: A Differential Test of Webhook Signature Verifiers Across Official SDKs and JavaScript Runtimes*.

One synthetic case set (83 signed deliveries across four schemes) goes to every verifier. Each verdict is recorded as one of:

- **accept:** returned without error.
- **reject:** a typed verification error or a false return.
- **crash:** any other exception.

The schemes are:

| Scheme | Header | Signed string | MAC |
|---|---|---|---|
| S (Stripe) | `t=..,v1=..` | `t.body` | hex |
| W (Standard Webhooks / Svix) | `v1,<base64>` | `id.ts.body` | `whsec_` key |
| K (Slack) | `v0=..` | `v0:ts:body` | hex |
| G (GitHub) | `sha256=..` | the body | hex |

All secrets are generated locally. No provider account, key or network call to any provider is used.

## Subjects (versions as run 2026-11-03)

- **CPython 3.13.5:** stripe 16.1.0, standardwebhooks 1.1.0, svix 2.9.1, slack_sdk 3.46.0 (`requirements.txt`, full freeze in `results/pip_freeze.txt`).
- **JavaScript** (`js/package.json` and `js/package-lock.json`; `results/npm_ls.txt`): stripe 23.1.0 (`constructEvent` and `constructEventAsync`), standardwebhooks 1.1.1, svix 2.9.1, @octokit/webhooks-methods 6.0.0, @slack/bolt 5.1.0 (`verifySlackRequest`).
- **JavaScript runtimes:**
  - Node v24.22.1.
  - Bun 1.4.2.
  - workerd 1.20261103.1 via `wrangler dev` 4.157.0, local only, with `nodejs_compat`. Bolt is not run in workerd.

## Files

- `gen_cases.py`: writes `cases.json`. Each case has an id, scheme, class (control, canonicalization, parsing or config), headers, body, secret and a reference verdict (accept, reject or unspecified) from the scheme's documentation. Timestamps are taken relative to generation time.
- `py/run_py.py`: Python subjects.
- `js/subjects.mjs` and `js/run_node.mjs`: JavaScript subjects under Node or Bun.
- `js/worker.mjs`, `js/wrangler.toml` and `js/run_workerd.sh`: the same subjects inside workerd. `run_workerd.sh` starts `wrangler dev` with setsid on 127.0.0.1:18787 and stops only its own process group.
- `run_all.sh`: the full matrix, run `REPS` times (default 2). Each run regenerates the cases.
- `analyze.py`: writes `results/summary.json` and `results/matrix.md`.
- `stability.sh`: runs 10 more fresh case sets through CPython, Node and Bun and lists any verdict that changes between sets (`results/stability.txt`). It then runs `py/nopad_sweep.py`, which uses 2,000 random bodies to measure how often an unpadded base64url signature crashes rather than rejects the Python Standard Webhooks and Svix verifiers (`results/nopad_sweep.txt`).
- `results/rep1/` and `results/rep2/`: raw verdict rows from the original run.

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
(cd js && npm ci)            # bun must also be on PATH
PY=.venv/bin/python ./run_all.sh
PY=.venv/bin/python ./stability.sh   # optional
```

## Original run

- 2 repetitions, identical verdicts, 502 verdicts per repetition (21 verifier-runtime pairs).
- 38 of the 83 cases drew more than one verdict. Excluding sync `constructEvent` on Bun and workerd, which throws for every input there, 18 did.
- Stability check: 10 fresh case sets through CPython, Node and Bun (379 triples). Only `W-b64url_nopad` on the two Python Standard Webhooks verifiers changed: 7 crashes and 3 rejects, because the decoder drops `-` and `_`, so the outcome depends on the signature bytes. In the sweeps, 1,788 and 1,820 of 2,000 bodies crashed.
- Reference regrade (2026-11-03, after the run): `S-future_330`, `S-future_1d` and `S-ts_ms` were changed from reject to unspecified. Stripe's documentation explicitly rejects only "too old" timestamps. The stored `cases.json` and `*.jsonl` files carry the updated `ref`; the verdicts are unchanged.
- No case let a delivery verify without a valid HMAC under the receiver's secret.
