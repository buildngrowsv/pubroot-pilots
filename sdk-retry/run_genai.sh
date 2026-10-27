#!/usr/bin/env bash
# Re-run of google-genai only, after fixing a harness bug (client object was garbage-collected before the call).
set -u; cd "$(dirname "$0")"
CERT=$(./gen_localhost_cert.sh)   # throwaway localhost cert, generated at run time (see README)
mkdir -p results
STUB_LOG=results/attempts.jsonl .venv/bin/python src/stub_server.py > results/stub_genai.log 2>&1 &
SP=$!; sleep 1
for rep in 1 2 3; do for sc in e500 timeout drop; do
  timeout 600 .venv/bin/python src/call_sdk.py google-genai "g$rep-google-genai" $sc >> results/client.jsonl 2>>results/client_stderr.log || echo "{\"sdk\":\"google-genai\",\"run_id\":\"g$rep-google-genai\",\"scenario\":\"$sc\",\"error\":\"harness timeout/crash\"}" >> results/client.jsonl
done; done
kill $SP; echo done
