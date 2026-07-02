# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building waypaper.exe (Windows).
Usage:
    pip install pyinstaller flask
    pyinstaller waypaper-windows.spec
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/waypaper/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/waypaper/static/index.html', 'waypaper/static'),
        ('src/waypaper/static/style.css', 'waypaper/static'),
        ('src/waypaper/static/app.js', 'waypaper/static'),
    ],
    hiddenimports=[
        'waypaper.web',
        'waypaper.brain',
        'waypaper.changer_windows',
        'waypaper.wallhaven',
        'waypaper.config',
        'waypaper.common',
        'flask',
        'PIL',
        'PIL._imaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'gi', 'PyGObject', 'cairo', 'Pango', 'Gdk', 'Gtk',
        'waypaper.app', 'waypaper.changer', 'waypaper.translations', 'waypaper.options',
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='waypaper.ico' if Path('waypaper.ico').exists() else None,
)
