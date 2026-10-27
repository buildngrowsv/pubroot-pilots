#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#13790 (worker and a trimmed test from the issue body). usage: run.sh old|new
set -u; d=$1; mkdir -p $d/src/test; cd $d
cat > src/index.ts <<'T'
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const m = url.pathname.match(/^\/debug-s(\d+)$/);
    if (m) { const status = parseInt(m[1], 10); const headers: Record<string, string> = {};
      if (status >= 300 && status < 400) headers["Location"] = url.searchParams.get("to") || "/";
      return new Response(null, { status, headers }); }
    if (url.pathname === "/missing") return new Response("Not Found", { status: 404 });
    return new Response("Hello, world!", { status: 200 });
  },
};
T
cat > src/test/repro.test.ts <<'T'
import { it, expect } from "vitest";
import { env, exports } from "cloudflare:workers";
import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
const worker = exports.default as any;
for (const mode of ["follow", "manual"] as const) {
  it(`302 with redirect=${mode}`, async () => {
    const req = mode === "follow" ? new Request("http://localhost/debug-s302?to=/missing") : new Request("http://localhost/debug-s302?to=/missing", { redirect: "manual" });
    const ctx = createExecutionContext(); const res = await worker.fetch(req, env, ctx); await waitOnExecutionContext(ctx);
    console.log(`OBSERVED redirect=${mode} status=${res.status}`); expect(res.status).toBe(302);
  });
}
T
echo '{"name":"r13790","main":"src/index.ts","compatibility_date":"2026-04-01","compatibility_flags":["nodejs_compat"]}' > wrangler.jsonc
if [ $1 = old ]; then
  printf 'import { cloudflareTest } from "@cloudflare/vitest-pool-workers";\nimport { defineConfig } from "vitest/config";\nexport default defineConfig({ plugins: [cloudflareTest({ wrangler: { configPath: "./wrangler.jsonc" } })] });\n' > vitest.config.ts
  PKGS="@cloudflare/vitest-pool-workers@~0.15.0 vitest@4.1.5 wrangler@4.86.0"
else
  printf 'import { cloudflareTest } from "@cloudflare/vitest-plugin";\nimport { defineConfig } from "vitest/config";\nexport default defineConfig({ plugins: [cloudflareTest({ wrangler: { configPath: "./wrangler.jsonc" } })] });\n' > vitest.config.ts
  PKGS="@cloudflare/vitest-plugin vitest@4.1.12 wrangler@4.152.0"
fi
[ -d node_modules ] || { npm init -y >/dev/null; npm pkg set type=module; npm i -s --legacy-peer-deps --no-audit --no-fund $PKGS > install.log 2>&1; }
timeout 180 npx vitest run > test.log 2>&1; echo "RESULT $1 exit=$?"; grep -E "OBSERVED|Error:|Tests " test.log | sort -u | head -6
