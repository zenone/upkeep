#!/bin/bash
# Stop all Upkeep services
# Useful for troubleshooting or clean shutdown
# API-First Design: Idempotent, handles all edge cases automatically

echo "🛑 Stopping Upkeep Services"
echo ""

# Stop web server (any Upkeep uvicorn process)
echo "🌐 Checking web server..."
WEB_PIDS=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)
if [ -n "$WEB_PIDS" ]; then
    echo "   Found web server process(es): $(echo $WEB_PIDS | tr '\n' ' ')"

    # Try graceful shutdown first (SIGTERM)
    echo "   Attempting graceful shutdown..."
    echo "$WEB_PIDS" | xargs kill -TERM 2>/dev/null

    # Wait up to 3 seconds for graceful shutdown
    sleep 1
    for i in {1..2}; do
        WEB_PIDS=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)
        if [ -z "$WEB_PIDS" ]; then
            echo "   ✅ Web server stopped cleanly"
            break
        fi
        sleep 1
    done

    # Force kill if still running
    WEB_PIDS=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)
    if [ -n "$WEB_PIDS" ]; then
        echo "   Force stopping unresponsive processes..."
        echo "$WEB_PIDS" | xargs kill -9 2>/dev/null
        echo "   ✅ Web server force stopped"
    fi
else
    echo "   ℹ️  No web server running"
fi
echo ""

# Stop daemon
echo "🔧 Checking daemon..."

# Check if daemon is running (no sudo needed for checking)
DAEMON_RUNNING=0
if launchctl list 2>/dev/null | grep -q "com.upkeep.daemon"; then
    DAEMON_RUNNING=1
elif sudo -n launchctl list 2>/dev/null | grep -q "com.upkeep.daemon"; then
    # Check system domain if we have cached sudo credentials
    DAEMON_RUNNING=1
fi

if [ "$DAEMON_RUNNING" -eq 1 ]; then
    echo "   Found daemon running"

    # NOW ask for password to stop it
    PLIST_PATH="/Library/LaunchDaemons/com.upkeep.daemon.plist"
    if [ -f "$PLIST_PATH" ]; then
        sudo launchctl unload "$PLIST_PATH" 2>/dev/null && echo "   ✅ Daemon stopped" || echo "   ⚠️  Failed to stop daemon"
    else
        echo "   ⚠️  Plist not found at $PLIST_PATH"
    fi
else
    echo "   ℹ️  No daemon running"
fi
echo ""

# Clean up job queue (optional)
QUEUE_DIR="/var/local/upkeep-jobs"
if [ -d "$QUEUE_DIR" ]; then
    # Check job counts (try without sudo first, fall back to sudo if needed)
    JOB_COUNT=$(find "$QUEUE_DIR" -name "*.job.json" 2>/dev/null | wc -l | tr -d ' ')
    RESULT_COUNT=$(find "$QUEUE_DIR" -name "*.result.json" 2>/dev/null | wc -l | tr -d ' ')

    # If we couldn't read without sudo, try with sudo -n (non-interactive)
    if [ "$JOB_COUNT" -eq 0 ] && [ "$RESULT_COUNT" -eq 0 ]; then
        if sudo -n ls "$QUEUE_DIR" >/dev/null 2>&1; then
            JOB_COUNT=$(sudo find "$QUEUE_DIR" -name "*.job.json" 2>/dev/null | wc -l | tr -d ' ')
            RESULT_COUNT=$(sudo find "$QUEUE_DIR" -name "*.result.json" 2>/dev/null | wc -l | tr -d ' ')
        fi
    fi

    if [ "$JOB_COUNT" -gt 0 ] || [ "$RESULT_COUNT" -gt 0 ]; then
        echo "🗑️  Job queue cleanup:"
        echo "   Jobs pending: $JOB_COUNT"
        echo "   Results cached: $RESULT_COUNT"

        if [ "$JOB_COUNT" -gt 0 ]; then
            echo "   ⚠️  Warning: $JOB_COUNT pending jobs will be deleted"
        fi

        read -p "   Clean up job queue? (y/n): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # NOW ask for password to clean (if not already have sudo cached)
            sudo rm -f "$QUEUE_DIR"/*.job.json 2>/dev/null || true
            sudo rm -f "$QUEUE_DIR"/*.result.json 2>/dev/null || true
            echo "   ✅ Job queue cleaned"
        else
            echo "   ℹ️  Job queue preserved"
        fi
    else
        echo "🗑️  Job queue is empty"
    fi
fi
echo ""

echo "✅ Shutdown complete"
echo ""
echo "To restart:"
echo "   Daemon:     sudo ./install-daemon.sh"
echo "   Web server: ./run-web.sh"
