#!/bin/bash
# Launch Upkeep web interface
# Server runs as normal user - authentication is handled via web UI

set -e
set -o pipefail

# Ensure output is not buffered
export PYTHONUNBUFFERED=1

# Function to find available port
find_available_port() {
    # Use Python script to find available port (8080-8089)
    local port=$(python3 find_port.py 2>/dev/null)
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo "❌ No available ports in range 8080-8089"
        echo ""
        echo "Ports in use:"
        for p in {8080..8089}; do
            local pid=$(lsof -ti:$p 2>/dev/null | head -n 1)
            if [ -n "$pid" ]; then
                local cmd=$(ps -p "$pid" -o command= 2>/dev/null | head -c 60)
                echo "  Port $p: $cmd"
            fi
        done
        echo ""
        echo "💡 Close some applications or manually kill processes:"
        echo "   lsof -ti:8080 | xargs kill -9"
        exit 1
    fi

    echo "$port"
}

# Function to stop existing Upkeep servers
stop_existing_servers() {
    # Check for running Upkeep web servers (uvicorn process)
    local pids=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)

    if [ -n "$pids" ]; then
        echo "🔍 Found running Upkeep server(s)"
        echo "🛑 Stopping existing instances..."
        echo ""

        # Try graceful shutdown first (SIGTERM)
        echo "$pids" | while read -r pid; do
            if kill -TERM "$pid" 2>/dev/null; then
                echo "   Sent shutdown signal to PID $pid"
            fi
        done

        # Wait up to 5 seconds for processes to stop
        local waited=0
        while [ $waited -lt 5 ]; do
            pids=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)
            if [ -z "$pids" ]; then
                echo "✅ Previous instances stopped cleanly"
                echo ""
                return 0
            fi
            sleep 1
            waited=$((waited + 1))
        done

        # Force kill if still running
        pids=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "⚠️  Forcing shutdown of unresponsive processes..."
            echo "$pids" | xargs kill -9 2>/dev/null
            sleep 1
            echo "✅ Previous instances terminated"
            echo ""
        fi
    fi
}

echo "🔧 Upkeep"
echo ""

# Set PYTHONPATH for validation check
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Validate prerequisites
if [ ! -d ".venv" ] || ! .venv/bin/python -c "import upkeep" 2>/dev/null; then
    echo "❌ Setup required"
    echo ""
    if [ ! -d ".venv" ]; then
        echo "Missing: Virtual environment"
        echo "   python3 -m venv .venv"
    fi
    if [ -d ".venv" ] && ! .venv/bin/python -c "import upkeep" 2>/dev/null; then
        echo "Missing: Package installation"
        echo "   source .venv/bin/activate && pip install -e ."
    fi
    exit 1
fi
echo "✓ Prerequisites OK"

# Build TypeScript frontend
echo "🔨 Building TypeScript frontend..."
if npm run build:web; then
    echo "✓ Frontend built"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Stop existing servers if any
pids=$(pgrep -f "uvicorn upkeep.web.server:app" 2>/dev/null) || true
if [ -n "$pids" ]; then
    echo "✓ Stopped previous instance"
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    sleep 1
fi

# Find available port
PORT=$(python3 find_port.py 2>&1) || { echo "❌ find_port.py failed"; exit 1; }
if [ -z "$PORT" ]; then
    echo "❌ No available ports (8080-8089 all in use)"
    exit 1
fi
echo "✓ Using port $PORT"

# Default to HTTP to avoid browser certificate warnings on localhost.
# Pass --https to force HTTPS if certificates are installed/trusted.
USE_HTTPS=false
if [ "${1:-}" = "--https" ]; then
    USE_HTTPS=true
fi

CERT_DIR="$HOME/.local/upkeep-certs"
CERT_FILE="$CERT_DIR/localhost.pem"
KEY_FILE="$CERT_DIR/localhost-key.pem"

if [ "$USE_HTTPS" = true ] && [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    # Check if cert is still valid (>30 days)
    expiry=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
    if [ -n "$expiry" ]; then
        expiry_epoch=$(date -j -f "%b %d %T %Y %Z" "$expiry" "+%s" 2>/dev/null || echo 0)
        now_epoch=$(date "+%s")
        days_left=$(( ($expiry_epoch - $now_epoch) / 86400 ))

        if [ $days_left -gt 30 ]; then
            HTTPS_ENABLED="true"
            echo "✓ HTTPS enabled ($days_left days remaining)"
        else
            HTTPS_ENABLED="false"
            echo "✓ HTTP mode (certificate expires in $days_left days)"
        fi
    else
        HTTPS_ENABLED="false"
        echo "✓ HTTP mode (certificate check failed)"
    fi
else
    HTTPS_ENABLED="false"
    echo "✓ HTTP mode (use ./run-web.sh --https to enable HTTPS if configured)"
fi
echo ""

# Check and update sudoers files if upkeep.sh changed (zero friction auto-update)
# This ensures SETENV tags and other sudoers changes are automatically applied
echo "🔒 Checking sudoers configuration..."
if [ -f "./upkeep.sh" ]; then
    # Check if upkeep.sh is newer than sudoers files (code updated = auto-regenerate)
    SUDOERS_OUTDATED=false

    if [ -f "/etc/sudoers.d/upkeep-mas" ]; then
        if [ "./upkeep.sh" -nt "/etc/sudoers.d/upkeep-mas" ]; then
            SUDOERS_OUTDATED=true
        fi
    fi

    if [ -f "/etc/sudoers.d/upkeep-homebrew" ]; then
        if [ "./upkeep.sh" -nt "/etc/sudoers.d/upkeep-homebrew" ]; then
            SUDOERS_OUTDATED=true
        fi
    fi

    if [ "$SUDOERS_OUTDATED" = true ]; then
        echo "   Detected upkeep.sh updates - regenerating sudoers files..."
        # Trigger setup by removing old files (upkeep.sh will auto-regenerate on next run)
        sudo rm -f /etc/sudoers.d/upkeep-mas 2>/dev/null || true
        sudo rm -f /etc/sudoers.d/upkeep-homebrew 2>/dev/null || true
        echo "   ✓ Sudoers will auto-regenerate on first operation"
    else
        echo "   ✓ Sudoers up-to-date"
    fi
fi
echo ""

# Check daemon status and auto-start if needed
DAEMON_RUNNING=false

# Check if daemon is running (not just installed)
if sudo -n launchctl list 2>/dev/null | grep -q "com.upkeep.daemon"; then
    # Daemon is loaded, check if actually running
    if pgrep -f "maintenance_daemon.py" >/dev/null 2>&1; then
        DAEMON_RUNNING=true
        echo "✓ Daemon running"
    else
        echo "⚠️  Daemon installed but not running"
    fi
elif launchctl list 2>/dev/null | grep -q "com.upkeep.daemon"; then
    # In user domain (shouldn't be)
    DAEMON_RUNNING=true
    echo "✓ Daemon running (user domain)"
fi

# Auto-start daemon if not running
if [ "$DAEMON_RUNNING" = false ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Daemon Setup Required"
    echo ""
    echo "The maintenance daemon enables:"
    echo "  • Running maintenance operations"
    echo "  • Scheduled maintenance tasks"
    echo "  • Background system operations"
    echo ""
    echo "This requires administrator privileges (one-time setup)."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Install daemon now? (y/n): " -n 1 -r
    echo ""
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if sudo ./install-daemon.sh; then
            DAEMON_RUNNING=true
            echo ""
            echo "✓ Daemon installed and running"
        else
            echo ""
            echo "⚠️  Daemon installation failed"
            echo "    Maintenance operations will not be available"
            echo "    You can install later with: sudo ./install-daemon.sh"
        fi
    else
        echo "⚠️  Skipping daemon installation"
        echo "    Maintenance operations will not be available"
        echo "    You can install later with: sudo ./install-daemon.sh"
    fi
    echo ""
fi

# Show status and URL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$HTTPS_ENABLED" = "true" ]; then
    echo "🚀 Server ready: https://localhost:$PORT"
else
    echo "🚀 Server ready: http://localhost:$PORT"
fi
echo ""
if [ "$DAEMON_RUNNING" = true ]; then
    echo "✓ Dashboard, Storage, Maintenance (full features)"
else
    echo "✓ Dashboard, Storage"
    echo "✗ Maintenance (daemon not running)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to handle shutdown
cleanup() {
    echo ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏹  Server stopped"
    echo ""

    # Check if daemon is running
    if pgrep -f "maintenance_daemon.py" >/dev/null 2>&1; then
        # Check for active scheduled tasks
        SCHEDULES_FILE="$HOME/.upkeep/schedules.json"
        ACTIVE_SCHEDULES=""
        if [ -f "$SCHEDULES_FILE" ]; then
            # Use Python to parse JSON and find enabled schedules
            ACTIVE_SCHEDULES=$(python3 <<EOF
import json
import sys
try:
    with open("$SCHEDULES_FILE") as f:
        schedules = json.load(f)
    enabled = [s for s in schedules if s.get("enabled", False)]
    if enabled:
        for s in enabled:
            name = s.get("name", "Unknown")
            next_run = s.get("next_run_display", "Unknown")
            print(f"   • {name} (next run: {next_run})")
except:
    pass
EOF
)
        fi

        # Show prompt with context
        if [ -n "$ACTIVE_SCHEDULES" ]; then
            echo "ℹ️  Daemon is managing scheduled maintenance tasks:"
            echo "$ACTIVE_SCHEDULES"
            echo ""
            echo "⚠️  Stopping daemon will disable these schedules."
            echo ""
        fi

        read -p "Stop daemon too? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if sudo launchctl unload /Library/LaunchDaemons/com.upkeep.daemon.plist 2>/dev/null; then
                echo "✓ Daemon stopped"
                if [ -n "$ACTIVE_SCHEDULES" ]; then
                    echo "⚠️  Scheduled maintenance tasks are now disabled"
                fi
            else
                echo "⚠️  Failed to stop daemon"
            fi
        else
            echo "✓ Daemon still running (auto-starts on reboot)"
        fi
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Activate virtual environment (already validated at start)
source .venv/bin/activate

# PYTHONPATH already set during validation

# Function to open browser (runs in background after server starts)
open_browser() {
    # Wait for server to be ready
    sleep 2

    # Build URL
    if [ "$HTTPS_ENABLED" = "true" ]; then
        URL="https://localhost:$PORT"
    else
        URL="http://localhost:$PORT"
    fi

    # Open browser (cross-platform)
    if command -v open >/dev/null 2>&1; then
        # macOS
        open "$URL" 2>/dev/null
    elif command -v xdg-open >/dev/null 2>&1; then
        # Linux
        xdg-open "$URL" 2>/dev/null
    elif command -v start >/dev/null 2>&1; then
        # Windows (Git Bash)
        start "$URL" 2>/dev/null
    fi
}

# Auto-open browser (can be disabled with: AUTO_OPEN_BROWSER=false ./run-web.sh)
if [ "${AUTO_OPEN_BROWSER:-true}" = "true" ]; then
    open_browser &
fi

# Run server (silent start - uvicorn will show startup)
# DEVELOPMENT mode enables auto-reload (set DEVELOPMENT=true for dev work)
# Production mode disables auto-reload to prevent breaking long-running operations
RELOAD_FLAG=""
if [ "${DEVELOPMENT:-false}" = "true" ]; then
    RELOAD_FLAG="--reload"
    echo "⚠️  Development mode: Auto-reload enabled (may interrupt long operations)"
    echo ""
fi

if [ "$HTTPS_ENABLED" = "true" ]; then
    # Start with HTTPS (use explicit venv path for reliability after sudo)
    .venv/bin/python -m uvicorn upkeep.web.server:app \
        --host 127.0.0.1 \
        --port "$PORT" \
        --ssl-keyfile "$KEY_FILE" \
        --ssl-certfile "$CERT_FILE" \
        $RELOAD_FLAG
else
    # Start with HTTP (use explicit venv path for reliability after sudo)
    .venv/bin/python -m uvicorn upkeep.web.server:app \
        --host 127.0.0.1 \
        --port "$PORT" \
        $RELOAD_FLAG
fi
