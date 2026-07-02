# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building waypaper.exe (Windows).
Produces a single .exe that bundles Flask, web UI, and all dependencies.

Usage:
    pip install pyinstaller
    pyinstaller --clean waypaper-windows.spec
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Static files (dest, source, typecode) ─────────────────────────────
static_datas = []
for f in Path("src/waypaper/static").rglob("*"):
    if f.is_file():
        rel = str(f.relative_to(Path("src/waypaper").parent))
        static_datas.append((rel, str(f), 'DATA'))

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
        'waypaper.app', 'waypaper.changer', 'waypaper.translations',
        'waypaper.options', 'waypaper.keybindings', 'waypaper.common',
        'tcl', 'tkinter', 'tk',
        'test', 'unittest',
        'numpy', 'matplotlib', 'scipy', 'pandas',
        'setuptools', 'pip', 'wheel',
        'cv2', 'opencv',
        'PyQt5', 'PySide2', 'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── Collect all submodules for Flask + deps ───────────────────────────
for pkg in ('flask', 'werkzeug', 'jinja2', 'markupsafe', 'PIL', 'certifi'):
    a.hiddenimports += collect_submodules(pkg)

# ── Collect data files (certifi cacert.pem, Flask templates, etc.) ────
# collect_data_files returns [(source, dest)] — we convert to (dest, source, 'DATA')
for pkg in ('certifi', 'flask', 'jinja2'):
    for src, dest in collect_data_files(pkg):
        a.datas.append((dest, src, 'DATA'))

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
