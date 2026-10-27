#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#12706 (config and worker from the issue body; browser check replaced by headers + body sniff). usage: run.sh <wrangler-ver>
set -u; d=v_$1; mkdir -p $d/src $d/public; cd $d
echo '{"name":"r12706","main":"src/index.ts","compatibility_date":"2026-02-01","assets":{"directory":"./public","binding":"ASSETS","not_found_handling":"single-page-application"}}' > wrangler.jsonc
cat > src/index.ts <<'T'
export default {
  async fetch(request, env, _ctx): Promise<Response> {
    const url = new URL(request.url)
    if (url.pathname.startsWith('/api/')) { return new Response('API endpoint', { status: 200 }) }
    return env.ASSETS.fetch(request)
  },
}
T
printf '<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>t</title></head><body><h1>Hello</h1><p>para</p></body></html>\n' > public/index.html
[ -d node_modules ] || { npm init -y >/dev/null; npm i -s --legacy-peer-deps --no-audit --no-fund wrangler@$1 > install.log 2>&1; }
setsid timeout 60 npx wrangler dev --port 18127 > dev.log 2>&1 & S=$!; for i in $(seq 1 40); do curl -s -o /dev/null localhost:18127/api/x && break; sleep 1; done
H=$(curl -s -D - -o body.html localhost:18127/ | tr -d '\r' | grep -i '^content-type'); echo "RESULT wrangler@$1 GET / $H; body_starts=$(head -c 15 body.html); escaped_tags=$(grep -c '&lt;' body.html)"
kill -TERM -- -$S 2>/dev/null; wait $S 2>/dev/null; sleep 2   # stops only the process group started above
