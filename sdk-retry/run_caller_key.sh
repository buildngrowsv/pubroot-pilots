#!/usr/bin/env bash
# Mitigation check: same stub scenarios, but the caller passes its own Idempotency-Key via extra_headers.
set -u; cd "$(dirname "$0")"
CERT=$(./gen_localhost_cert.sh)   # throwaway localhost cert, generated at run time (see README)
mkdir -p results
STUB_LOG=results/attempts.jsonl .venv/bin/python src/stub_server.py > results/stub_ck.log 2>&1 &
SP=$!; sleep 1
for sdk in openai anthropic groq together; do for sc in e500 timeout drop; do
  CALLER_KEY=1 timeout 120 .venv/bin/python src/call_sdk.py $sdk "k1-$sdk" $sc >> results/client_callerkey.jsonl 2>>results/client_stderr.log
done; done
kill $SP; echo done
