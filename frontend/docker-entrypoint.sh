#!/bin/sh
set -e
# Prefer Next.js standalone server when `output: "standalone"` produced `.next/standalone/`.
if [ -f ./.next/standalone/server.js ]; then
  cd .next/standalone
  exec node server.js
fi
if [ -f ./server.js ]; then
  exec node server.js
fi
exec npm run start -- --hostname 0.0.0.0 --port 3000
