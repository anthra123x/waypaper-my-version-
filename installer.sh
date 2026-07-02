#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.config/waypaper"
LIBRARY_DIR="${HOME}/Imágenes/wallpapers"

echo "=== Waypaper — Wallhaven Browser Edition installer ==="

# 1. System dependencies check
echo "[1/5] Verificando dependencias..."
if ! command -v pipx &>/dev/null; then
    echo "  pipx no encontrado. Instalalo primero:"
    echo "  Debian/Ubuntu: sudo apt install pipx"
    echo "  Arch:          sudo pacman -S pipx"
    exit 1
fi
echo "  ✓ pipx encontrado"

# 2. Install waypaper from local source via pipx
echo "[2/5] Instalando waypaper desde src/..."
pipx install --force "${REPO_DIR}" 2>&1 | tail -3
echo "  ✓ waypaper instalado"

# 3. Install helper scripts
echo "[3/5] Instalando scripts helper..."
mkdir -p "${BIN}"
for script in wallhaven-download wallpaper-brain; do
    cp "${REPO_DIR}/scripts/${script}" "${BIN}/"
    chmod +x "${BIN}/${script}"
    echo "  ✓ ${script}"
done

# 4. Install config files
echo "[4/5] Instalando configuracion..."
mkdir -p "${CONFIG_DIR}"
if [ -f "${REPO_DIR}/config/style.css" ]; then
    cp "${REPO_DIR}/config/style.css" "${CONFIG_DIR}/style.css"
    echo "  ✓ style.css"
fi
if [ -f "${REPO_DIR}/config/config.ini.example" ] && [ ! -f "${CONFIG_DIR}/config.ini" ]; then
    cp "${REPO_DIR}/config/config.ini.example" "${CONFIG_DIR}/config.ini"
    echo "  ✓ config.ini (nuevo)"
elif [ -f "${CONFIG_DIR}/config.ini" ]; then
    echo "  - config.ini ya existe, se conserva"
fi

# 5. Create library folder
echo "[5/5] Creando carpeta de wallpapers guardados..."
mkdir -p "${LIBRARY_DIR}"
echo "  ✓ ${LIBRARY_DIR}"

# Clean up any old systemd timers that auto-download
for unit in wallpaper-brain.timer wallhaven-fetch.timer; do
    unit_path="${HOME}/.config/systemd/user/${unit}"
    if [ -f "${unit_path}" ]; then
        echo "  - Desactivando timer legacy: ${unit}"
        systemctl --user disable "${unit}" 2>/dev/null || true
        systemctl --user stop "${unit}" 2>/dev/null || true
        rm -f "${unit_path}"
    fi
done
systemctl --user daemon-reload 2>/dev/null || true

# Desktop entry
echo "[+] Instalando entry de escritorio..."
mkdir -p "${HOME}/.local/share/applications"
cat > "${HOME}/.local/share/applications/waypaper.desktop" << DESKTOP
[Desktop Entry]
Name=Waypaper (Browser Edition)
Comment=Wallhaven wallpaper browser with preview dialog and library
Exec=${BIN}/waypaper
Type=Application
Categories=Utility;
Icon=waypaper
DESKTOP
echo "  ✓ waypaper.desktop"

echo ""
echo "=== Instalacion completa ==="
echo "Ejecuta:  waypaper"
echo ""
echo "Atajos en Waypaper:"
echo "  hjkl    -> Navegacion"
echo "  Enter   -> Set wallpaper / abrir preview"
echo "  d       -> Discard / borrar de biblioteca"
echo "  y       -> Save to library"
echo "  r       -> Refresh"
echo "  g / G   -> Ir al inicio / final"
