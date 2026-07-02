# Waypaper — Wallhaven Browser Edition

Fork de [Waypaper](https://github.com/anufrievroman/waypaper) 2.8 convertido en un navegador visual de [Wallhaven](https://wallhaven.cc). Sin escaneo local, sin thumbnails en disco. Cada thumbnail se descarga en memoria y se muestra progresivamente. La descarga completa solo ocurre cuando hacés clic.

Cross-platform: **GTK3 en Linux**, **Flask + Web UI en Windows** — el mismo binario detecta el SO y arranca el backend correspondiente.

## Features

- **API-first**: navegá Wallhaven por categoría (Random, Anime, Manga, Sketch, General)
- **Preview dialog**: clic en thumbnail → preview con Set Wallpaper / Save to Library
- **Library mode**: sección "♥ Kept" muestra solo tus wallpapers guardados localmente
- **Wallpaper Brain**: motor de preferencias Keep/Discard que aprende de tus elecciones
- **Filtros**: All / ♥ Kept / ✕ Discarded / ◇ New con búsqueda por texto
- **Keyboard shortcuts**: `hjkl` navegación, `Enter` set, `d` discard, `y` save
- **Sin descargas automáticas**: solo se descarga lo que elegís explícitamente
- **Cross-platform**: GTK3 en Linux, Web UI (Flask) en Windows

## Instalación — Linux

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

## Instalación — Windows

### Opción 1: .exe descargable (recomendado)

Descargá `waypaper.exe` desde los **Actions** del repo:
1. Andá a [Actions → Build Windows .exe](https://github.com/anthra123x/waypaper-my-version-/actions/workflows/build-windows.yml)
2. Hacé clic en el último workflow exitoso
3. Scrolleá abajo a **Artifacts** y descargá `waypaper-windows.zip`
4. Descomprimí y ejecutá `waypaper.exe`

No requiere Python ni ninguna dependencia. El .exe es completamente standalone.

> También podés generar tu propio .exe con Python (ver Opción 2).

### Opción 2: desde código fuente (requiere Python 3.11+)

```powershell
git clone https://github.com/anthra123x/waypaper-my-version-.git
cd waypaper-my-version-
pip install . flask
python -m waypaper
```

Esto arranca un servidor Flask en `http://localhost:5000` y abre tu navegador.

### Build tu propio .exe

```powershell
pip install pyinstaller flask
pip install .
pyinstaller --clean waypaper-windows.spec
```

El ejecutable se genera en `dist\waypaper.exe`. Funciona en cualquier PC con Windows 10+.

## Uso

```bash
# Linux — GTK GUI
waypaper                          # abre el GUI en modo biblioteca (tus saved)
waypaper --random                 # setea un wallpaper aleatorio desde terminal

# Windows — Web UI
python -m waypaper                # arranca Flask + abre el browser
```

### Keyboard shortcuts — GTK (Linux)

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

### Keyboard shortcuts — Web UI (Windows)

| Tecla | Acción |
|---|---|
| `hjkl` | Navegación en grilla |
| `←` `→` | Página anterior / siguiente |
| `Enter` | Set wallpaper |
| `d` | Discard |
| `y` | Delete from library |
| `s` | Save to library |
| `K` / `Escape` | Cerrar preview |
| `r` | Refresh |
| `1` | Modo Search |
| `2` | Modo Library |

## Scripts

| Script | Descripción |
|---|---|
| `wallhaven-download` | CLI para descargar de Wallhaven por preset + tags |
| `wallpaper-brain` | Motor de preferencias: keep/discard/recommend/cleanup |
| `waypaper-gnome` | Wrapper que ejecuta cleanup+recommend, abre GUI, aplica wallpaper |
| `waypaper-refresh` | Descarga N wallpapers y abre el GUI |
| `build-windows.sh` | Build helper para empaquetar .exe con PyInstaller |

## Modificaciones respecto a Waypaper original

- **Sin escaneo de carpetas locales**: toda la navegación es vía API de Wallhaven
- **Preview dialog**: reemplaza el set inmediato al hacer clic (modal con Set/Save/Cancel)
- **Library mode**: la sección Kept carga wallpapers guardados en `~/Imágenes/wallpapers/`
- **Startup**: abre mostrando la biblioteca local, no resultados aleatorios de API
- **Discard en biblioteca**: elimina el archivo físico del disco
- **wallpaper-brain**: registro de preferencias, pesos de tags, recomendaciones (extraído a `brain.py`)
- **Status bar**: muestra stats del brain (kept/discarded/tags) y modo actual
- **Temp cache**: se limpia al iniciar la app
- **Windows support**: `__main__.py` detecta el SO y arranca Flask + Web UI en Windows

## Arquitectura

```
src/waypaper/
├── __main__.py      # Entrypoint: OS dispatch (Windows → web, Linux → GTK)
├── app.py           # GUI principal (GTK3) — toda la lógica nueva
├── wallhaven.py     # Cliente API Wallhaven + rate limiting
├── brain.py         # Motor de preferencias (Keep/Discard/Stats)
├── web.py           # Flask server con API REST (Windows)
├── changer.py       # Backends Linux: swww, swaybg, mpvpaper, etc.
├── changer_windows.py # Wallpaper setter Windows (ctypes + COM)
├── config.py        # Configuración cross-platform
├── common.py        # Utilidades varias
├── keybindings.py   # Mapeo de teclas GTK
├── translations.py  # Strings multi-idioma
├── options.py       # Opciones de backend disponibles
├── static/          # Web UI (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
└── ...

scripts/
├── wallpaper-brain     # CLI wrapper que importa de brain.py
└── wallhaven-download  # CLI de descarga directa

waypaper-windows.spec   # PyInstaller spec para .exe
build-windows.sh        # Build helper
```

### Cómo funciona el dispatch

`__main__.py` verifica `os.name` al arrancar:
- **Windows**: importa `web.start_server()` → Flask en `http://localhost:5000` → abre el browser
- **Linux**: importa `Config`, `App`, etc. → GTK GUI (comportamiento original)

### Endpoints de la API REST (Windows)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Web UI (index.html) |
| `GET` | `/api/search` | Buscar en Wallhaven |
| `GET` | `/api/thumb/<id>` | Proxy de thumbnail |
| `GET` | `/api/thumb_local/<name>` | Thumbnail de archivo local |
| `GET` | `/api/temp/<name>` | Archivo temporal (preview) |
| `GET` | `/api/library` | Listar biblioteca local |
| `GET` | `/api/status` | Stats del brain (o status por ?id=) |
| `POST` | `/api/download/<id>` | Descargar full-res a temp |
| `POST` | `/api/set/<id>` | Guardar + setear wallpaper |
| `POST` | `/api/save/<id>` | Guardar a biblioteca + keep |
| `POST` | `/api/discard/<id>` | Descartar en brain |
| `POST` | `/api/keep/<id>` | Marcar como kept |
| `DELETE` | `/api/library/<id>` | Eliminar archivo + forget |

## Almacenamiento

- **Wallpapers guardados**: `~/Imágenes/wallpapers/` (Linux) / `%USERPROFILE%\Pictures\wallpapers\` (Windows)
- **Preferencias (brain)**: `~/.config/waypaper/preferences.json` (Linux) / `%APPDATA%\waypaper\preferences.json` (Windows)
- **Temp cache**: `~/.cache/waypaper/temp/` (se limpia al iniciar)
- **Nombres**: `wh-{id}.{jpg,png}` — el stem `wh-{id}` vincula al ID de Wallhaven

## Licencia

GPL v3 — mismo licenciamiento que el Waypaper original de Roman Anufriev.
