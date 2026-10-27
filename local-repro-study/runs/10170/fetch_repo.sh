#!/usr/bin/env bash
# Clone the reporter's public repo for cloudflare/workers-sdk#10170 at the commit used in the pilot.
set -eu
[ -d repo ] || git clone -q https://github.com/mw10013/cloudflare-react-router-vitest repo
git -C repo checkout -q 81eaadf878659cd944b536bd2fdaa55ff2df94bf
