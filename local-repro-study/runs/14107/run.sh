#!/usr/bin/env bash
# Replay of cloudflare/workers-sdk#14107 inside a directory whose path contains a space.
# usage: run.sh old|new
set -u; d="My Project/$1"; mkdir -p "$d/src"; cd "$d"
printf 'name = "repro"\nmain = "src/index.ts"\ncompatibility_date = "2025-01-01"\n' > wrangler.toml
# EDIT (not in the issue text): the pool 0.5 rejects configs without nodejs_compat, so it is added.
printf 'compatibility_flags = ["nodejs_compat"]\n' >> wrangler.toml
echo 'export default { fetch() { return new Response("ok"); } };' > src/index.ts
printf 'import { expect, it } from "vitest";\nit("smoke", () => { expect(1).toBe(1); });\n' > src/x.test.ts
if [ "$1" = old ]; then
  printf 'import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";\nexport default defineWorkersConfig({ test: { poolOptions: { workers: { wrangler: { configPath: "./wrangler.toml" } } } } });\n' > vitest.config.ts
  PKGS="vitest@~2.1 @cloudflare/vitest-pool-workers@^0.5 wrangler@^4"
else
  printf 'import { cloudflareTest } from "@cloudflare/vitest-plugin";\nimport { defineConfig } from "vitest/config";\nexport default defineConfig({ plugins: [cloudflareTest({ wrangler: { configPath: "./wrangler.toml" } })] });\n' > vitest.config.ts
  PKGS="vitest@4.1.12 @cloudflare/vitest-plugin wrangler@4.152.0"
fi
[ -d node_modules ] || { npm init -y >/dev/null; npm pkg set type=module; npm i -s --legacy-peer-deps --no-audit --no-fund $PKGS > install.log 2>&1; }
timeout 180 npx vitest run > test.log 2>&1; echo "RESULT $1 exit=$?"; grep -m3 -E "No such module|%2520|Tests .*passed|Error" test.log
