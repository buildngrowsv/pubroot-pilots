#!/usr/bin/env bash
# Kill only this pilot's own process group (recorded by env.sh). Never a broad pkill.
HERE=$(cd "$(dirname "$0")" && pwd); PG=$(cat $HERE/run/pgid 2>/dev/null) || exit 0
[ -n "$PG" ] && kill -TERM -- -$PG 2>/dev/null; sleep 1; kill -KILL -- -$PG 2>/dev/null; rm -f $HERE/run/pgid; echo "stopped pgid $PG"
