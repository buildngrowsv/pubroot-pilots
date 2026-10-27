#!/usr/bin/env bash
# Fetches the two stefanbuck/github-issue-parser versions under test at pinned commits (not committed here;
# third-party code is not vendored in this repo). Each clone gets its own `npm ci` for its dependencies.
set -eu
cd "$(dirname "$0")"
mkdir -p vendor
fetch() {  # dir sha label
  if [ ! -d "vendor/$1/.git" ]; then git clone -q https://github.com/stefanbuck/github-issue-parser.git "vendor/$1"; fi
  git -C "vendor/$1" checkout -q "$2"
  (cd "vendor/$1" && npm ci --silent --ignore-scripts)
  echo "vendor/$1 -> $(git -C "vendor/$1" rev-parse HEAD) ($3)"
}
fetch stefanbuck        cb6e97157cbf851e3a393ff8d57c93a484cc323f v3.2.5
fetch stefanbuck-v3.2.4 0d9ce93802360bd2925bc2cc4be1d807ed1d1233 v3.2.4
