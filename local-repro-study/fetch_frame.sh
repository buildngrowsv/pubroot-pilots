#!/usr/bin/env bash
# Re-fetch the sampling frame (full issue bodies) from the public GitHub search API into data/frame_raw.json.
# Unauthenticated; no token needed. Issues edited after 2026-10-26 may change the frame slightly.
set -eu
Q=$(head -1 data/frame_query.txt)
curl -sS -G "https://api.github.com/search/issues" --data-urlencode "q=$Q" --data-urlencode "per_page=100" \
  -H "Accept: application/vnd.github+json" -o data/frame_raw.json
python3 -c "import json;d=json.load(open('data/frame_raw.json'));print(d['total_count'],'issues')"
