#!/bin/bash
# NETPROBE Auto-Installer untuk Termux
# Usage: bash install.sh

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  NETPROBE Installer — Termux Edition                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if running on Termux
if [ ! -d "$PREFIX" ] || [ "$TERMUX_APP_PID" == "" ]; then
    echo "⚠️  Mungkin tidak running di Termux — tapi tetap lanjut..."
fi

echo "Step 1: Update package manager..."
pkg update -y
if [ $? -ne 0 ]; then
    echo "❌ Failed to update packages"
    exit 1
fi

echo ""
echo "Step 2: Install Python dan dependencies sistem..."
pkg install -y python3 python3-pip git curl
if [ $? -ne 0 ]; then
    echo "❌ Failed to install system packages"
    exit 1
fi

echo ""
echo "Step 3: Create NETPROBE directory..."
mkdir -p ~/netprobe
cd ~/netprobe
echo "✓ Directory: $(pwd)"

echo ""
echo "Step 4: Install Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    echo "Try: pip install flask flask-cors dnspython requests"
    exit 1
fi

echo ""
echo "Step 5: Verify installation..."
python3 -c "import flask; import dnspython; import requests" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All Python modules imported successfully"
else
    echo "❌ Some modules failed to import"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Installation Complete! ✓                                ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Next steps:                                             ║"
echo "║  1. cd ~/netprobe                                        ║"
echo "║  2. python3 backend.py                                   ║"
echo "║  3. Open browser: http://localhost:5000                  ║"
echo "║                                                          ║"
echo "║  Or read SETUP_TERMUX.md untuk detail lebih lengkap.    ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
