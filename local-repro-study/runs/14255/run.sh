#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#14255 (config and worker copied from the issue body). usage: run.sh <wrangler-ver>
set -u; d=v_$1; mkdir -p $d/src $d/dist/client; cd $d
cat > wrangler.toml <<'T'
name = "spa-repro"
main = "src/index.ts"
compatibility_date = "2026-04-01"

[dev]
port = 18099

[assets]
directory = "./dist/client"
binding = "ASSETS"
run_worker_first = ["/api/*"]
not_found_handling = "single-page-application"

[[routes]]
pattern = "spa-repro.example.com"
custom_domain = true

[env.test]
T
cat > src/index.ts <<'T'
export default {
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname.startsWith("/api/")) {
      return new Response(JSON.stringify({ ok: true, path: url.pathname }), { headers: { "content-type": "application/json" } });
    }
    return new Response("worker 404", { status: 404 });
  },
};
T
echo '<!doctype html><title>spa</title><p>index</p>' > dist/client/index.html
[ -d node_modules ] || { npm init -y >/dev/null; npm i -s --legacy-peer-deps --no-audit --no-fund wrangler@$1 > install.log 2>&1; }
setsid timeout 60 npx wrangler dev --env test --port 18099 > dev.log 2>&1 & S=$!; for i in $(seq 1 40); do curl -s -o /dev/null localhost:18099/api/x && break; sleep 1; done
for p in / /projects; do echo "RESULT wrangler@$1 GET $p -> $(curl -s -o /dev/null -w '%{http_code}' localhost:18099$p)"; done
kill -TERM -- -$S 2>/dev/null; wait $S 2>/dev/null; sleep 2   # only our process group (wrangler + its workerd)
