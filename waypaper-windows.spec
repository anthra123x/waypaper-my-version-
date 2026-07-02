# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building waypaper.exe (Windows).
Produces a single .exe that bundles Flask, web UI, and all dependencies.

Usage:
    pip install pyinstaller flask
    pyinstaller --clean waypaper-windows.spec

The resulting dist/waypaper.exe is fully standalone.
"""

import sys
from pathlib import Path

block_cipher = None

# Collect all static files
static_dir = Path("src/waypaper/static")
static_datas = []
for f in static_dir.rglob("*"):
    if f.is_file():
        rel = f.relative_to(Path("src/waypaper"))
        static_datas.append((str(f), str(rel.parent)))

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
        'flask',
        'jinja2',
        'markupsafe',
        'werkzeug',
        'PIL',
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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    console=False,              # Windows GUI app (no terminal window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
