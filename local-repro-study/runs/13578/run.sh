#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#13578. usage: run.sh <vite-plugin-ver> <vite-ver> <wrangler-ver>
set -u; d=v_$1; mkdir -p $d/src; cd $d
cat > src/index.ts <<'TS'
import { Hono } from "hono";
const app = new Hono();
app.post("/api/auth/login", async (c) => { await c.req.json(); return c.json({ error: "bad credentials" }, 401); });
app.post("/api/other", async (c) => { await c.req.json(); return c.json({ error: "forbidden" }, 403); });
export default { fetch: app.fetch };
TS
echo '{"name":"r13578","main":"src/index.ts","compatibility_date":"2026-04-01"}' > wrangler.jsonc
echo 'import { defineConfig } from "vite"; import { cloudflare } from "@cloudflare/vite-plugin"; export default defineConfig({ plugins: [cloudflare()] });' > vite.config.ts
npm pkg set type=module >/dev/null 2>&1; [ -d node_modules ] || { npm init -y >/dev/null; npm pkg set type=module; npm i -s --no-audit --no-fund hono @cloudflare/vite-plugin@$1 vite@$2 wrangler@$3 >/dev/null 2>&1; }
PORT=$((5170 + RANDOM % 50)); setsid timeout 90 npx vite --port $PORT --strictPort > vite.log 2>&1 & S=$!; for i in $(seq 1 60); do curl -s -o /dev/null localhost:$PORT && break; sleep 1; done
for p in other auth/login; do echo "RESULT POST /api/$p -> $(curl -s -o /dev/null -w '%{http_code}' -X POST localhost:$PORT/api/$p -H 'Content-Type: application/json' -d '{"x":1}')"; done
kill -TERM -- -$S 2>/dev/null; wait $S 2>/dev/null;   # only our process group
 grep -m1 -i "fetch failed" vite.log
