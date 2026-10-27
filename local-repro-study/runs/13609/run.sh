#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#13609 using the public gist linked in the issue. usage: run.sh <wrangler-ver>
set -u; ./fetch_gist.sh; d=v_$1; mkdir -p $d/src; cp gist/wrangler.jsonc gist/echo-server.mjs $d/; cp gist/index.ts $d/src/index.ts; cd $d   # gists are flat; main is src/index.ts
[ -d node_modules ] || { npm init -y >/dev/null; npm pkg set type=module; npm i -s --legacy-peer-deps --no-audit --no-fund wrangler@$1 > install.log 2>&1; }
node echo-server.mjs 9192 1000 > echo.log 2>&1 & E=$!
setsid timeout 90 npx wrangler dev --port 9191 > dev.log 2>&1 & S=$!; for i in $(seq 1 40); do curl -s -o /dev/null localhost:9191/probe && break; sleep 1; done
for n in 20 100; do echo "RESULT wrangler@$1 $(curl -s "localhost:9191/storm?n=$n")"; done
kill -TERM -- -$S 2>/dev/null; kill $E; wait 2>/dev/null; sleep 3   # only processes started above
