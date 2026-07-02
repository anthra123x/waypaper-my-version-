"""Windows wallpaper changer via Win32 API and COM (Windows 8+ multi-monitor)."""

import ctypes
import ctypes.wintypes
import os
from pathlib import Path

SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATE_INI_FILE = 0x01
SPIF_SENDWININICHANGE = 0x02


def _get_com_interface():
    """Try to load IDesktopWallpaper (Windows 8+) for per-monitor support."""
    try:
        from ctypes import com
        # Try via ctypes.com (Python 3.14+)
        try:
            from ctypes.com import interfaces
            CLSID_DesktopWallpaper = "{c2cf3110-460e-4fc1-b8d0-8a1c0c9cc4bd}"
            IID_IDesktopWallpaper = "{b92b56a9-8b55-4e14-9a89-0199bbb6f93b}"
            dw = com.CreateObject(CLSID_DesktopWallpaper, interface=IID_IDesktopWallpaper)
            return dw
        except (ImportError, AttributeError):
            pass
    except Exception:
        pass
    return None


def set_wallpaper(path: str | Path) -> bool:
    """Set wallpaper for all monitors using SystemParametersInfoW.

    On Windows 8+ also tries per-monitor via IDesktopWallpaper.
    Returns True on success.
    """
    path_str = str(Path(path).resolve())
    if not os.path.isfile(path_str):
        return False

    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, path_str,
        SPIF_UPDATE_INI_FILE | SPIF_SENDWININICHANGE,
    )
    return bool(result)


def get_supported_extensions() -> list[str]:
    """Return list of extensions supported by Windows for wallpaper."""
    return [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]


def is_supported(path: str | Path) -> bool:
    ext = Path(path).suffix.lower()
    return ext in get_supported_extensions()
