#!/bin/bash
# Alternative TUI launcher that runs Python as root
# This ensures all subprocess calls have elevated privileges without needing keep-alive

echo "🔧 macOS Maintenance Toolkit - TUI Launcher (Root Mode)"
echo ""
echo "⚠️  This will run the TUI as root (all operations will have sudo privileges)"
echo "   You will be prompted for your password once."
echo ""

# Activate venv and set PYTHONPATH
source .venv/bin/activate
export PYTHONPATH=/Users/szenone/Documents/CODE/BASH/upkeep/src:$PYTHONPATH

# Run the entire Python TUI as root
# This way all subprocess.run() calls inherit root privileges
echo "Launching TUI as root..."
sudo -E env "PATH=$PATH" "PYTHONPATH=$PYTHONPATH" upkeep tui

# Note: -E preserves environment variables
# "PATH=$PATH" ensures the venv python is used
# "PYTHONPATH=$PYTHONPATH" ensures module imports work

echo ""
echo "TUI exited."
