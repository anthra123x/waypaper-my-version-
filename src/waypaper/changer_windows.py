"""Windows wallpaper changer via SystemParametersInfoW (Win32 API)."""

import ctypes
import os
from pathlib import Path

SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATE_INI_FILE = 0x01
SPIF_SENDWININICHANGE = 0x02


def set_wallpaper(path: str | Path) -> bool:
    """Set wallpaper via Win32 SystemParametersInfoW."""
    path_str = str(Path(path).resolve())
    if not os.path.isfile(path_str):
        return False
    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path_str,
        SPIF_UPDATE_INI_FILE | SPIF_SENDWININICHANGE,
    )
    return bool(result)


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
