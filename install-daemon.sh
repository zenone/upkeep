#!/bin/bash
# Install Upkeep Daemon
#
# This script installs a root-privileged launchd daemon that executes
# maintenance operations securely. Run once with sudo.
#
# Security: Daemon uses job queue for IPC, no password handling needed.

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run with sudo"
    echo "Usage: sudo ./install-daemon.sh"
    exit 1
fi

echo "🔧 Upkeep Daemon Installer"
echo ""
echo "This will install a privileged maintenance daemon that:"
echo "  • Runs as a launchd service (root privileges)"
echo "  • Executes maintenance operations securely"
echo "  • Uses job queue for communication (no passwords needed)"
echo ""

# Determine script location and source directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running from Homebrew installation (libexec/) or source
if [ -d "$SCRIPT_DIR/src/daemon" ]; then
    # Homebrew layout: daemon in libexec/src/daemon/, upkeep.sh in libexec/
    DAEMON_DIR="$SCRIPT_DIR/src/daemon"
    # upkeep.sh is installed directly to libexec/ by Homebrew formula
    if [ -f "$SCRIPT_DIR/upkeep.sh" ]; then
        UPKEEP_SH="$SCRIPT_DIR/upkeep.sh"
    else
        UPKEEP_SH="$SCRIPT_DIR/src/upkeep.sh"
    fi
elif [ -d "$SCRIPT_DIR/daemon" ]; then
    # Source layout: ./daemon/
    DAEMON_DIR="$SCRIPT_DIR/daemon"
    UPKEEP_SH="$SCRIPT_DIR/upkeep.sh"
elif [ -d "./daemon" ]; then
    # Running from project root
    DAEMON_DIR="./daemon"
    UPKEEP_SH="./upkeep.sh"
else
    echo "❌ Error: Cannot find source files"
    echo "Run this script from the project root or via Homebrew:"
    echo "  sudo \$(brew --prefix upkeep)/libexec/install-daemon.sh"
    exit 1
fi

# Directories
LIB_DIR="/usr/local/lib/upkeep"
QUEUE_DIR="/var/local/upkeep-jobs"
PLIST_SRC="$DAEMON_DIR/com.upkeep.daemon.plist"
PLIST_DST="/Library/LaunchDaemons/com.upkeep.daemon.plist"
DAEMON_SRC="$DAEMON_DIR/upkeep_daemon.py"
DAEMON_DST="$LIB_DIR/upkeep_daemon.py"
MAINTAIN_SH_SRC="$UPKEEP_SH"
MAINTAIN_SH_DST="$LIB_DIR/upkeep.sh"

# Check source files exist
if [ ! -f "$DAEMON_SRC" ]; then
    echo "❌ Error: $DAEMON_SRC not found"
    echo "Source directory: $SRC_DIR"
    exit 1
fi

if [ ! -f "$MAINTAIN_SH_SRC" ]; then
    echo "❌ Error: $MAINTAIN_SH_SRC not found"
    exit 1
fi

if [ ! -f "$PLIST_SRC" ]; then
    echo "❌ Error: $PLIST_SRC not found"
    exit 1
fi

echo "📁 Creating directories..."
mkdir -p "$LIB_DIR"
mkdir -p "$QUEUE_DIR"

echo "📋 Installing daemon files..."
# Install daemon
cp "$DAEMON_SRC" "$DAEMON_DST"
chmod 755 "$DAEMON_DST"
chown root:wheel "$DAEMON_DST"

# Install upkeep.sh
cp "$MAINTAIN_SH_SRC" "$MAINTAIN_SH_DST"
chmod 755 "$MAINTAIN_SH_DST"
chown root:wheel "$MAINTAIN_SH_DST"

# Install plist
cp "$PLIST_SRC" "$PLIST_DST"
chmod 644 "$PLIST_DST"
chown root:wheel "$PLIST_DST"

echo "🔒 Setting permissions..."
# Queue directory: rwxrwxrwx (world-writable so web backend can enqueue jobs)
# This is safe since it's localhost-only and only accepts JSON job files
chmod 777 "$QUEUE_DIR"
chown root:wheel "$QUEUE_DIR"

# Check if daemon is already running - auto-update without prompting
echo "🔄 Configuring launchd..."
if launchctl list | grep -q "com.upkeep.daemon"; then
    echo "   Updating existing daemon..."
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    sleep 1
    echo "   ✓ Previous version unloaded"
fi

# Load daemon
echo "   Loading daemon..."
launchctl load "$PLIST_DST"

# Wait a moment for daemon to start
sleep 2

# Check if daemon is running
if launchctl list | grep -q "com.upkeep.daemon"; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "Daemon Status:"
    launchctl list | grep com.upkeep.daemon || echo "   (daemon info unavailable)"
    echo ""
    echo "Files Installed:"
    echo "   Daemon: $DAEMON_DST"
    echo "   Script: $MAINTAIN_SH_DST"
    echo "   Plist:  $PLIST_DST"
    echo "   Queue:  $QUEUE_DIR"
    echo ""
    echo "Logs:"
    echo "   Output: /var/log/upkeep-daemon.log"
    echo "   Errors: /var/log/upkeep-daemon.err"
    echo ""
    echo "✓ Daemon is ready to accept jobs."
    echo "✓ Auto-starts on system reboot (launchd service)."
    echo ""
    echo "🌐 Next Steps:"
    echo "   1. Start the web server: ./run-web.sh"
    echo "   2. The server will display the URL (HTTP or HTTPS)"
    echo "   3. No passwords needed - daemon handles privileged operations!"
else
    echo ""
    echo "⚠️  Daemon may not be running. Check logs:"
    echo "   sudo tail -f /var/log/upkeep-daemon.err"
    exit 1
fi
