#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.config/waypaper"
SYSTEMD_USER="${HOME}/.config/systemd/user"

echo "=== waypaper-my-version installer ==="

# 1. Install/upgrade Waypaper from local source via pipx
echo "[1/5] Instalando waypaper desde src/..."
if command -v pipx &>/dev/null; then
    pipx install --force "${REPO_DIR}" 2>&1 | tail -3
    echo "  ✓ waypaper instalado desde el repositorio local"
else
    echo "  ✗ pipx no encontrado. Instalá python3-pipx primero."
    exit 1
fi

# 2. Install helper scripts
echo "[2/5] Instalando scripts helper..."
mkdir -p "${BIN}"
for script in wallhaven-download wallpaper-brain waypaper-gnome waypaper-refresh; do
    cp "${REPO_DIR}/scripts/${script}" "${BIN}/"
    chmod +x "${BIN}/${script}"
    echo "  ✓ ${script}"
done

# 3. Install config files
echo "[3/5] Instalando configuracion..."
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

# 4. Install systemd timers
echo "[4/5] Instalando timers systemd..."
mkdir -p "${SYSTEMD_USER}"
for unit in wallpaper-brain.service wallpaper-brain.timer; do
    cp "${REPO_DIR}/systemd/${unit}" "${SYSTEMD_USER}/"
    echo "  ✓ ${unit}"
done
systemctl --user daemon-reload
systemctl --user enable --now wallpaper-brain.timer 2>&1 | tail -2

# 5. Desktop entry + autostart
echo "[5/5] Instalando entry de escritorio..."
mkdir -p "${HOME}/.local/share/applications" "${HOME}/.config/autostart"

cat > "${HOME}/.local/share/applications/waypaper.desktop" << DESKTOP
[Desktop Entry]
Name=Waypaper (my-version)
Comment=Wallhaven-integrated wallpaper setter with recommendation engine
Exec=${BIN}/waypaper-gnome
Type=Application
Categories=Utility;
Icon=waypaper
DESKTOP

cat > "${HOME}/.config/autostart/waypaper.desktop" << AUTOSTART
[Desktop Entry]
Name=Waypaper restore
Comment=Restore wallpaper on login
Exec=${BIN}/waypaper-gnome --restore
Type=Application
NoDisplay=true
X-GNOME-Autostart-enabled=true
AUTOSTART

echo "  ✓ waypaper.desktop (menu + autostart)"

# Bash aliases
echo "[+] Agregando aliases a ~/.bashrc..."
for entry in 'alias waypaper="waypaper-gnome"' \
             'alias wallhaven-download="wallhaven-download"' \
             'alias wallpaper-brain="wallpaper-brain"' \
             'alias waypaper-refresh="waypaper-refresh"'; do
    if ! grep -qxF "${entry}" "${HOME}/.bashrc" 2>/dev/null; then
        echo "${entry}" >> "${HOME}/.bashrc"
    fi
done
echo "  ✓ aliases agregados"

echo ""
echo "=== Instalacion completa ==="
echo "Usa:  waypaper         # abre el GUI con recomendaciones frescas"
echo "      waypaper-refresh  # descarga N nuevos wallpapers + abre GUI"
echo "      wallpaper-brain   # CLI del motor de preferencias"
echo "      wallpaper-brain status   # ver stats"
echo ""
echo "Atajos en Waypaper:"
echo "  Mayus+K  -> Keep (borde verde)"
echo "  D        -> Discard (borde rojo)"
echo "  R        -> Refresh (descarga nuevas recomendaciones)"
echo ""
echo "Timer: wallpaper-brain.timer corre cada 20 min (cleanup + recommend)"
