# Waypaper — Wallhaven Browser Edition

Fork de [Waypaper](https://github.com/anufrievroman/waypaper) 2.8 convertido en un navegador visual de [Wallhaven](https://wallhaven.cc). Sin escaneo local, sin thumbnails en disco. Cada thumbnail se descarga en memoria y se muestra progresivamente. La descarga completa solo ocurre cuando hacés clic.

## Features

- **API-first**: navegá Wallhaven por categoría (Random, Anime, Manga, Sketch, General)
- **Preview dialog**: clic en thumbnail → preview con Set Wallpaper / Save to Library
- **Library mode**: sección "♥ Kept" muestra solo tus wallpapers guardados localmente
- **Wallpaper Brain**: motor de preferencias Keep/Discard que aprende de tus elecciones
- **Filtros**: All / ♥ Kept / ✕ Discarded / ◇ New con búsqueda por texto
- **Keyboard shortcuts**: `hjkl` navegación, `Enter` set, `d` discard, `y` save, `K` keep
- **Sin descargas automáticas**: solo se descarga lo que elegís explícitamente

## Instalación rápida

Requiere Python 3.11+ y `pipx`.

```bash
git clone https://github.com/anthra123x/waypaper-my-version-.git
cd waypaper-my-version-
chmod +x installer.sh
./installer.sh
```

### Manual

```bash
# 1. Instalar el paquete Python
pipx install --force .

# 2. Copiar scripts auxiliares
mkdir -p ~/.local/bin
cp scripts/* ~/.local/bin/
chmod +x ~/.local/bin/*

# 3. Copiar CSS
mkdir -p ~/.config/waypaper
cp config/style.css ~/.config/waypaper/

# 4. Crear carpeta de wallpapers guardados
mkdir -p ~/Imágenes/wallpapers
```

### Dependencias del sistema (Debian/Ubuntu)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 pipx
```

### Dependencias del sistema (Arch)

```bash
sudo pacman -S python-gobject gtk3 pipx
```

## Uso

```bash
waypaper                          # abre el GUI en modo biblioteca (tus saved)
waypaper --random                 # setea un wallpaper aleatorio desde terminal
```

### Keyboard shortcuts

| Tecla | Acción |
|---|---|
| `hjkl` | Navegación (←↓↑→) |
| `Enter` | Set wallpaper (descarga si es necesario) |
| `d` | Discard (borra de biblioteca si es local) |
| `y` | Save to library |
| `K` | Keep (registra como kept en brain) |
| `g` / `G` | Ir al inicio / final |
| `r` | Refresh (recarga API o biblioteca) |
| `/` | Focus búsqueda |

## Scripts

| Script | Descripción |
|---|---|
| `wallhaven-download` | CLI para descargar de Wallhaven por preset + tags |
| `wallpaper-brain` | Motor de preferencias: keep/discard/recommend/cleanup |
| `waypaper-gnome` | Wrapper que ejecuta cleanup+recommend, abre GUI, aplica wallpaper |
| `waypaper-refresh` | Descarga N wallpapers y abre el GUI |

## Modificaciones respecto a Waypaper original

- **Sin escaneo de carpetas locales**: toda la navegación es vía API de Wallhaven
- **Preview dialog**: reemplaza el set inmediato al hacer clic (modal con Set/Save/Cancel)
- **Save button removido**: redundante con el preview dialog; atajo `y` conservado
- **Library mode**: la sección Kept carga wallpapers guardados en `~/Imágenes/wallpapers/`
- **Startup**: abre mostrando la biblioteca local, no resultados aleatorios de API
- **Discard en biblioteca**: elimina el archivo físico del disco
- **wallpaper-brain**: registro de preferencias, pesos de tags, recomendaciones
- **Status bar**: muestra stats del brain (kept/discarded/tags) y modo actual
- **Paginación**: oculta en modo biblioteca
- **Temp cache**: se limpia al iniciar la app

## Arquitectura

```
src/waypaper/
├── app.py          # GUI principal (GTK3) — toda la lógica nueva
├── wallhaven.py    # Cliente API Wallhaven + dataclass WallpaperItem
├── config.py       # Configuración de Waypaper original
├── changer.py      # Backends: swww, swaybg, mpvpaper, etc.
├── keybindings.py  # Mapeo de teclas
├── translations.py # Strings multi-idioma
└── common.py       # Utilidades varias

scripts/
├── wallpaper-brain     # Motor de preferencias (Keep/Discard)
└── wallhaven-download  # CLI de descarga directa
```

Los wallpapers guardados se almacenan en `~/Imágenes/wallpapers/` con nombre `wh-{id}.{jpg,png}`. Las preferencias (kept/discarded, pesos de tags) se guardan en `~/.config/waypaper/preferences.json`.

## Licencia

GPL v3 — mismo licenciamiento que el Waypaper original de Roman Anufriev.
