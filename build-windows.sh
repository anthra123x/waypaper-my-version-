#!/usr/bin/env bash
#
# Build waypaper.exe for Windows using PyInstaller.
# Run this on Windows, or cross-compile with Wine/Python.
#
set -euo pipefail

echo "==> Installing Windows dependencies..."
pip install pyinstaller flask

echo "==> Building waypaper.exe..."
pyinstaller --clean waypaper-windows.spec

echo "==> Done!"
echo "    dist/waypaper.exe  —  standalone Windows executable"
echo "    (copy it anywhere; includes Flask + web UI)"
