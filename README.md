# waypaper-my-version

Fork personal de [Waypaper](https://github.com/anufrievroman/waypaper) 2.8 con integración Wallhaven + motor de recomendación por preferencias (Keep/Discard).

## Modificaciones al código original

### `src/waypaper/app.py`
- **Combo de categoría Wallhaven** en la barra superior (Random, Anime, Manga, Sketch, General)
- **Refresh button modificado**: descarga N wallpapers de Wallhaven antes de recargar el grid
- **Keyboard shortcuts**:
  - `Mayús+K` → marca el wallpaper seleccionado como **Keep** (borde verde)
  - `D` → marca como **Discard** (borde rojo + opacidad reducida)
- **Indicadores visuales** via CSS (ver `config/style.css`)
- **Search entry**: el texto ingresado se pasa como `-q` (tag search) al descargar

### `src/waypaper/keybindings.py`
- Agregados key bindings `keep_wallpaper` (K) y `discard_wallpaper` (d)

## Scripts incluidos

| Script | Descripción |
|---|---|
| `scripts/wallhaven-download` | Descarga wallpapers desde Wallhaven API por preset + tags |
| `scripts/wallpaper-brain` | Motor de preferencias: keep/discard/recommend/cleanup |
| `scripts/waypaper-gnome` | Wrapper que corre cleanup+recommend, abre GUI, y aplica wallpaper via gsettings |
| `scripts/waypaper-refresh` | Descarga N y abre el GUI directamente |

## Instalación

```bash
git clone https://github.com/anthra123x/waypaper-my-version-.git
cd waypaper-my-version-
chmod +x installer.sh
./installer.sh
```

O manualmente:

```bash
pipx install --force .
mkdir -p ~/.local/bin
cp scripts/* ~/.local/bin/
chmod +x ~/.local/bin/*
mkdir -p ~/.config/waypaper
cp config/style.css ~/.config/waypaper/
mkdir -p ~/.config/systemd/user
cp systemd/wallpaper-brain.* ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now wallpaper-brain.timer
```

## Uso

```bash
waypaper                           # abre el GUI (descarga recomendaciones primero)
waypaper-refresh anime 10          # descarga 10 de anime y abre
wallpaper-brain status             # ver estadisticas de preferencias
wallpaper-brain keep ~/ruta.jpg    # marcar como keep directamente
wallpaper-brain recommend 5        # forzar recomendacion de 5 nuevos
```

## Requisitos

- Python 3.11+
- pipx
- PyGObject + GTK4
- Pillow
- swaybg o mpvpaper (backends de Waypaper)

## Licencia

GPL — mismo licenciamiento que el Waypaper original de Roman Anufriev.
