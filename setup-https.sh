#!/bin/bash
# Setup HTTPS certificates for Upkeep web interface
# Uses mkcert for automatic local CA trust

set -e

CERT_DIR="$HOME/.local/upkeep-certs"
CERT_FILE="$CERT_DIR/localhost.pem"
KEY_FILE="$CERT_DIR/localhost-key.pem"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🔒 Upkeep - HTTPS Certificate Setup"
echo ""

# Check if mkcert is installed
if ! command -v mkcert &> /dev/null; then
    echo "📦 mkcert is not installed"
    echo ""
    echo "mkcert creates local HTTPS certificates that are automatically"
    echo "trusted by your browser (no security warnings)."
    echo ""
    echo "Installation:"

    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "  ✓ Homebrew detected"
        echo "  → Command: brew install mkcert"
        echo ""
        read -p "Install mkcert now? (y/n): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "📥 Installing mkcert via Homebrew..."
            if brew install mkcert; then
                echo "✅ mkcert installed successfully"
            else
                echo "❌ Failed to install mkcert"
                echo ""
                echo "💡 You can try manually:"
                echo "   brew install mkcert"
                echo ""
                echo "📖 Or visit: https://github.com/FiloSottile/mkcert"
                exit 1
            fi
        else
            echo ""
            echo "ℹ️  Skipping HTTPS setup"
            echo "   The web interface will use HTTP instead (http://localhost:8080)"
            exit 2
        fi
    else
        echo "  ✗ Homebrew not found"
        echo ""
        echo "Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
        echo "Then install mkcert:"
        echo "  brew install mkcert"
        echo ""
        echo "Or visit: https://github.com/FiloSottile/mkcert"
        exit 1
    fi
fi

echo "✅ mkcert is installed"
echo ""

# Check if local CA is installed and trusted
echo "🔍 Checking local Certificate Authority..."

# Always run mkcert -install to ensure CA is in system trust store
# This is idempotent - safe to run multiple times
echo "📝 Installing/Verifying local Certificate Authority..."
echo ""
echo "💡 This will:"
echo "   • Create a local CA (Certificate Authority) if needed"
echo "   • Add it to your system's trust store (Keychain)"
echo "   • Your password may be required"
echo ""

if mkcert -install; then
    echo "✅ Local CA installed/verified in system trust store"
else
    echo "❌ Failed to install local CA"
    exit 1
fi

echo ""

# Create cert directory
if [ ! -d "$CERT_DIR" ]; then
    echo "📁 Creating certificate directory..."
    mkdir -p "$CERT_DIR"
fi

# Check if certificates already exist and are valid
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "🔍 Checking existing certificates..."

    # Check expiration date (mkcert certs are valid for 10 years by default)
    EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
    EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY" "+%s" 2>/dev/null || echo 0)
    NOW_EPOCH=$(date "+%s")
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

    if [ $DAYS_LEFT -gt 30 ]; then
        echo "✅ Valid certificates found (expires in $DAYS_LEFT days)"
        echo ""
        echo "Certificate paths:"
        echo "  🔐 Certificate: $CERT_FILE"
        echo "  🔑 Private Key: $KEY_FILE"
        echo ""
        echo "✅ HTTPS setup complete!"
        exit 0
    else
        echo "⚠️  Certificates expire soon (in $DAYS_LEFT days)"
        echo "   Regenerating certificates..."
    fi
fi

# Generate new certificates
echo "🔧 Generating HTTPS certificates for localhost..."
echo ""

cd "$CERT_DIR"

if mkcert -cert-file localhost.pem -key-file localhost-key.pem localhost 127.0.0.1 ::1; then
    echo ""
    echo "✅ Certificates generated successfully!"
    echo ""
    echo "Certificate paths:"
    echo "  🔐 Certificate: $CERT_FILE"
    echo "  🔑 Private Key: $KEY_FILE"
    echo ""
    echo "These certificates are:"
    echo "  • Valid for 10 years"
    echo "  • Automatically trusted by all browsers"
    echo "  • Only work on your local machine (secure)"
    echo ""
    echo "✅ HTTPS setup complete!"
else
    echo ""
    echo "❌ Failed to generate certificates"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   1. Try running: mkcert -install"
    echo "   2. Check mkcert docs: https://github.com/FiloSottile/mkcert"
    exit 1
fi
