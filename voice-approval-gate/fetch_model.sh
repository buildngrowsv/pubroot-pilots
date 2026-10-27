#!/usr/bin/env bash
# Download the Vosk small English model used in the pilot and verify the zip's SHA-256. The model is not redistributed here.
set -eu
mkdir -p models && cd models
Z=vosk-model-small-en-us-0.15.zip
[ -f $Z ] || curl -sSL -o $Z https://alphacephei.com/vosk/models/$Z
echo "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498  $Z" | sha256sum -c -
[ -d vosk-model-small-en-us-0.15 ] || python3 -c "import zipfile;zipfile.ZipFile('$Z').extractall('.')"
