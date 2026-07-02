# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building waypaper.exe (Windows).
Produces a single .exe that bundles Flask, web UI, and all dependencies.

Usage:
    pip install pyinstaller
    pyinstaller --clean waypaper-windows.spec
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ── Static files ──────────────────────────────────────────────────────
static_dir = Path("src/waypaper/static")
static_datas = []
for f in static_dir.rglob("*"):
    if f.is_file():
        rel = f.relative_to(Path("src/waypaper"))
        static_datas.append((str(f), str(rel.parent)))

# ── Analysis ──────────────────────────────────────────────────────────
a = Analysis(
    ['src/waypaper/__main__.py'],
    pathex=[],
    binaries=[],
    datas=static_datas,
    hiddenimports=[
        'waypaper',
        'waypaper.web',
        'waypaper.brain',
        'waypaper.changer_windows',
        'waypaper.wallhaven',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'gi', 'gi.repository', 'PyGObject', 'cairo', 'pangocairo',
        'gtk', 'Gdk', 'Gtk', 'Pango',
        'waypaper.app',
        'waypaper.changer',
        'waypaper.translations',
        'waypaper.options',
        'waypaper.keybindings',
        'waypaper.common',
        'tkinter',
        'test',
        'numpy',
        'matplotlib',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── Collect all submodules for Flask and its dependencies ─────────────
for pkg in ('flask', 'werkzeug', 'jinja2', 'markupsafe', 'PIL', 'certifi'):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    a.datas += pkg_datas
    a.binaries += pkg_binaries
    a.hiddenimports += pkg_hidden

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='waypaper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
