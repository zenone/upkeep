#!/bin/bash
# Helper script to run TUI with correct PYTHONPATH for Python 3.14 and sudo keep-alive
# Uses proper sudo keep-alive pattern to maintain timestamp during long operations

echo "🔧 macOS Maintenance Toolkit - TUI Launcher"
echo ""

# Ask for sudo password upfront
echo "⚠️  Some maintenance operations require sudo privileges."
echo "   Please enter your password to cache sudo for this session:"
echo ""
sudo -v

# Keep-alive: update existing sudo timestamp until parent process exits
# Uses 'sudo -v' which actually refreshes the timestamp (not just checks it)
# The 'kill -0 "$$"' checks if parent script is still running
while true; do
    sudo -v
    sleep 60
    kill -0 "$$" || exit
done 2>/dev/null &

KEEPALIVE_PID=$!
echo "✓ sudo cached and keep-alive started (PID: $KEEPALIVE_PID)"
echo ""

# Cleanup function to kill keep-alive on exit
cleanup() {
    if [[ -n "$KEEPALIVE_PID" ]] && kill -0 "$KEEPALIVE_PID" 2>/dev/null; then
        echo ""
        echo "Stopping sudo keep-alive..."
        kill "$KEEPALIVE_PID" 2>/dev/null
        wait "$KEEPALIVE_PID" 2>/dev/null
    fi
}
trap cleanup EXIT INT TERM

echo "Launching TUI..."
source .venv/bin/activate
export PYTHONPATH=/Users/szenone/Documents/CODE/BASH/mac-maintenance/src:$PYTHONPATH
mac-maintenance tui

# Cleanup happens automatically via trap
