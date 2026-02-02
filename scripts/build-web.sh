#!/usr/bin/env bash
set -euo pipefail

# Build TypeScript frontend with ESBuild
echo "Building web frontend..."

npx esbuild src/mac_maintenance/web/static/ts/app.ts \
  --bundle \
  --target=es2020 \
  --platform=browser \
  --outfile=src/mac_maintenance/web/static/app.js \
  --sourcemap \
  --format=iife \
  --minify

echo "Build complete: src/mac_maintenance/web/static/app.js"
