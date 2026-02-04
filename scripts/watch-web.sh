#!/usr/bin/env bash
set -euo pipefail

# Watch TypeScript frontend and rebuild on changes
echo "Watching TypeScript files for changes..."
echo "Press Ctrl+C to stop"

npx esbuild src/upkeep/web/static/ts/app.ts \
  --bundle \
  --target=es2020 \
  --platform=browser \
  --outfile=src/upkeep/web/static/app.js \
  --sourcemap \
  --format=iife \
  --watch
