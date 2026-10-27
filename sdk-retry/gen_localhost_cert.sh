#!/usr/bin/env bash
# Generates a throwaway self-signed certificate for 127.0.0.1/localhost at run time.
# Only fal-client needs it (it always uses https); the stub serves TLS on port 8766.
# Output goes to .certs/ (git-ignored). Nothing here is committed; delete .certs/ when done.
set -eu
cd "$(dirname "$0")"
mkdir -p .certs && chmod 700 .certs
if [ ! -s .certs/cert.pem ]; then
  openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    -keyout .certs/key.pem -out .certs/cert.pem 2>/dev/null
  chmod 600 .certs/key.pem
fi
echo "$PWD/.certs/cert.pem"
