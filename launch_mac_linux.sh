#!/bin/bash
echo "============================================"
echo "  Among Us Mobile Auto Suite — Launcher"
echo "============================================"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found."
    echo "Install via: brew install python3  OR  sudo apt install python3"
    exit 1
fi

# Install deps
echo "Installing dependencies..."
pip3 install -r requirements.txt -q

# Launch
echo "Launching..."
python3 among_us_auto.py
