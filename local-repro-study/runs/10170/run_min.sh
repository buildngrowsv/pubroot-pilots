#!/usr/bin/env bash
# Maintainer's minimal repro from the issue thread. usage: run_min.sh <vite-plugin> <vitest> <vite>
set -u; d=min_$1_$2; mkdir -p $d/src; cd $d
echo 'export default { fetch() { return new Response("ok"); } };' > src/index.ts
echo '{"name":"r10170","main":"src/index.ts","compatibility_date":"2026-03-01"}' > wrangler.jsonc
printf 'import { cloudflare } from "@cloudflare/vite-plugin";\nimport { defineConfig } from "vitest/config";\nexport default defineConfig({ plugins: [cloudflare()], test: {} });\n' > vitest.config.ts
printf 'import { it, expect } from "vitest";\nit("smoke", () => { expect(1).toBe(1); });\n' > src/x.test.ts
[ -d node_modules ] || { npm init -y >/dev/null; npm pkg set type=module; npm i -s --legacy-peer-deps --no-audit --no-fund @cloudflare/vite-plugin@$1 vitest@$2 vite@$3 wrangler > install.log 2>&1; }
timeout 180 npx vitest run > test.log 2>&1; echo "RESULT exit=$?"; grep -m3 -E "ERROR|Error|Tests .*passed|failed" test.log
