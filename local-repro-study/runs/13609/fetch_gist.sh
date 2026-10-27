#!/usr/bin/env bash
# Fetch the public gist linked from cloudflare/workers-sdk#13609 (author: danieltroger) and check it
# matches the files used in the pilot (fetched 2026-10-26). The gist is not redistributed here.
set -eu
[ -d gist ] || git clone -q https://gist.github.com/danieltroger/d8bbdafd3d92d93b4d82cb29f0774147.git gist
(cd gist && sha256sum -c ../gist.sha256)
