#!/usr/bin/env bash
# usage: run.sh <miniflare-version>
set -u; d=v_$1; mkdir -p $d; cp repro.mjs $d/; cd $d
[ -d node_modules ] || { npm init -y >/dev/null; npm i -s --no-audit --no-fund miniflare@$1 >/dev/null 2>&1; }
timeout 120 node repro.mjs 2>&1 | grep -E "RESULT|Error" | head -3
