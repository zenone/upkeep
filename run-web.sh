#!/bin/bash
# Launch Upkeep web interface
# Server runs as normal user - authentication is handled via web UI
#
# Options:
#   --open    Auto-open browser on start (opt-in, like vite/webpack)
#   --https   Force HTTPS if certificates are installed

set -e
set -o pipefail

# Get script directory and cd to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure output is not buffered
export PYTHONUNBUFFERED=1

# Function to find available port
find_available_port() {
    # Use Python script to find available port (8080-8089)
    local port=$(python3 "$SCRIPT_DIR/find_port.py" 2>/dev/null)
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

# Auto-reinstall package if source changed (zero friction updates)
NEWEST_SRC=$(find src/upkeep -name "*.py" -newer .venv/lib/*/site-packages/upkeep*.dist-info 2>/dev/null | head -1)
if [ -n "$NEWEST_SRC" ]; then
    echo "🔄 Source code updated - reinstalling package..."
    source .venv/bin/activate && pip install -e . -q
    echo "✓ Package reinstalled"
fi

# Install Node.js dependencies if needed (for TypeScript build)
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies (first run)..."
    if npm install --silent; then
        echo "✓ Node.js dependencies installed"
    else
        echo "❌ Failed to install Node.js dependencies"
        echo "   Try running: npm install"
        exit 1
    fi
fi

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
PORT=$(python3 "$SCRIPT_DIR/find_port.py" 2>&1) || { echo "❌ find_port.py failed"; exit 1; }
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

# Check daemon status and detect if reload needed
DAEMON_RUNNING=false
DAEMON_NEEDS_RELOAD=false
DAEMON_PID=""

# Get daemon PID if running
DAEMON_PID=$(pgrep -f "upkeep_daemon.py" 2>/dev/null | head -1) || true

if [ -n "$DAEMON_PID" ]; then
    DAEMON_RUNNING=true
    
    # Check if source files are newer than running daemon process
    # (daemon has stale code in memory if source changed after it started)
    DAEMON_START_TIME=$(ps -p "$DAEMON_PID" -o lstart= 2>/dev/null)
    if [ -n "$DAEMON_START_TIME" ]; then
        # Convert to epoch for comparison
        DAEMON_EPOCH=$(date -j -f "%a %b %d %T %Y" "$DAEMON_START_TIME" "+%s" 2>/dev/null)
        
        if [ -n "$DAEMON_EPOCH" ]; then
            # Check daemon source files
            for src_file in "./daemon/upkeep_daemon.py" "./upkeep.sh"; do
                if [ -f "$src_file" ]; then
                    SRC_EPOCH=$(stat -f "%m" "$src_file" 2>/dev/null)
                    if [ -n "$SRC_EPOCH" ] && [ "$SRC_EPOCH" -gt "$DAEMON_EPOCH" ]; then
                        DAEMON_NEEDS_RELOAD=true
                        break
                    fi
                fi
            done
        fi
    fi
fi

# Handle daemon state
if [ "$DAEMON_NEEDS_RELOAD" = true ]; then
    echo "🔄 Daemon code changed since last start"
    echo "   Reloading daemon with fresh code..."
    echo ""
    if sudo ./install-daemon.sh; then
        echo ""
        echo "✓ Daemon reloaded"
    else
        echo ""
        echo "⚠️  Daemon reload failed. Run: sudo ./install-daemon.sh"
    fi
    echo ""
elif [ "$DAEMON_RUNNING" = true ]; then
    echo "✓ Daemon running (up-to-date)"
else
    # Daemon not running - check if source is newer than installed (first-time install case)
    INSTALLED_DAEMON="/usr/local/lib/upkeep/upkeep_daemon.py"
    NEEDS_INSTALL=false
    
    if [ ! -f "$INSTALLED_DAEMON" ]; then
        NEEDS_INSTALL=true
    elif [ -f "./daemon/upkeep_daemon.py" ] && [ "./daemon/upkeep_daemon.py" -nt "$INSTALLED_DAEMON" ]; then
        NEEDS_INSTALL=true
    fi
    
    if [ "$NEEDS_INSTALL" = true ] || [ ! -f "/Library/LaunchDaemons/com.upkeep.daemon.plist" ]; then
        echo "🔧 Installing maintenance daemon..."
        if sudo ./install-daemon.sh; then
            DAEMON_RUNNING=true
            echo ""
            echo "✓ Daemon installed"
        else
            echo "⚠️  Daemon installation failed"
        fi
        echo ""
    else
        # Installed but not running - start it
        echo "🔄 Starting daemon..."
        if sudo launchctl load /Library/LaunchDaemons/com.upkeep.daemon.plist 2>/dev/null; then
            DAEMON_RUNNING=true
            echo "✓ Daemon started"
        else
            echo "⚠️  Failed to start daemon"
        fi
        echo ""
    fi
fi

# Auto-install daemon if not running (zero friction - no prompts)
if [ "$DAEMON_RUNNING" = false ]; then
    echo ""
    echo "🔧 Installing maintenance daemon (one-time setup)..."
    echo "   This enables maintenance operations & scheduling."
    echo ""
    
    if sudo ./install-daemon.sh; then
        DAEMON_RUNNING=true
        echo ""
        echo "✓ Daemon installed and running"
    else
        echo ""
        echo "⚠️  Daemon installation failed"
        echo "    Maintenance operations will not be available until installed."
        echo "    Try: sudo ./install-daemon.sh"
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
echo ""
echo "💡 Tip: Use --open to auto-open browser"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to handle shutdown
cleanup() {
    echo ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⏹  Server stopped"
    
    # Check if daemon is running and show status (no prompt)
    if pgrep -f "upkeep_daemon.py" >/dev/null 2>&1; then
        echo "✓ Daemon continues running (handles scheduled tasks)"
        echo ""
        echo "💡 To stop daemon: sudo launchctl unload /Library/LaunchDaemons/com.upkeep.daemon.plist"
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

# Parse --open flag for browser auto-open (opt-in, matching vite/webpack convention)
OPEN_BROWSER=false
for arg in "$@"; do
    case "$arg" in
        --open) OPEN_BROWSER=true ;;
    esac
done

# Also support legacy env var (AUTO_OPEN_BROWSER=true ./run-web.sh)
if [ "${AUTO_OPEN_BROWSER:-}" = "true" ]; then
    OPEN_BROWSER=true
fi

if [ "$OPEN_BROWSER" = "true" ]; then
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
