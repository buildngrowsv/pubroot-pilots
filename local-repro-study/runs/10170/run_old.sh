#!/usr/bin/env bash
# "Before" replay of #10170: the reporter's repo at 81eaadf with its pnpm lockfile (vite-plugin 1.11.0, vitest 3.2.4).
set -u; ./fetch_repo.sh; cd repo
pnpm install --frozen-lockfile > ../install.log 2>&1
timeout 180 pnpm test > ../test_old.log 2>&1; echo "RESULT old exit=$?"; grep -m3 -E "ERROR|Tests .*passed|failed" ../test_old.log
