#!/usr/bin/env bash
# Runs every SDK x scenario x rep against the local stub. $0, no network beyond 127.0.0.1.
set -u
cd "$(dirname "$0")"
CERT=$(./gen_localhost_cert.sh)   # throwaway localhost cert, generated at run time (see README)
mkdir -p results
rm -f results/attempts.jsonl results/client.jsonl
STUB_LOG=results/attempts.jsonl .venv/bin/python src/stub_server.py > results/stub.log 2>&1 &
SP=$!; sleep 1
for rep in 1 2 3; do for sdk in openai anthropic groq together mistralai cohere google-genai replicate fal-client; do for sc in e500 timeout drop; do
  SSL_CERT_FILE=$CERT timeout 300 .venv/bin/python src/call_sdk.py $sdk "r$rep-$sdk" $sc >> results/client.jsonl 2>>results/client_stderr.log || echo "{\"sdk\":\"$sdk\",\"run_id\":\"r$rep-$sdk\",\"scenario\":\"$sc\",\"error\":\"harness timeout/crash\"}" >> results/client.jsonl
done; done; done
kill $SP
echo done
