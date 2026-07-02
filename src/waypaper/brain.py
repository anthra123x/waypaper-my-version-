"""Wallpaper preference engine — keep/discard/tags/status logic.

Can be imported by both the CLI script (wallpaper-brain) and the web server (web.py).
Paths are auto-detected for Linux (%USERPROFILE% on Windows).
"""

import hashlib
import json
import os
import random
import time
import urllib.request
from pathlib import Path


def _appdir() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", "")) / "waypaper"
    return Path.home() / ".config" / "waypaper"


def _library_dir() -> Path:
    if os.name == "nt":
        return Path.home() / "Pictures" / "wallpapers"
    return Path.home() / "Imágenes" / "wallpapers"


PREFS_PATH = _appdir() / "preferences.json"
LIBRARY_DIR = _library_dir()


def default_prefs() -> dict:
    return {
        "kept": {},
        "discarded": {},
        "tag_weights": {},
        "tag_count": 0,
        "last_cleanup": "",
        "last_recommend": "",
    }


def load_prefs() -> dict:
    if PREFS_PATH.exists():
        try:
            return json.loads(PREFS_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return default_prefs()


def save_prefs(prefs: dict) -> None:
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(prefs, indent=2, ensure_ascii=False))


def wid_from(path) -> str:
    n = Path(path).stem
    if n.startswith("wh-"):
        return n[3:]
    local_id = hashlib.md5(str(path).encode()).hexdigest()[:12]
    return f"local_{local_id}"


def fetch_tags(wid: str) -> list[str]:
    if not wid or wid.startswith("local_"):
        return []
    try:
        req = urllib.request.Request(
            f"https://wallhaven.cc/api/v1/w/{wid}",
            headers={"User-Agent": "waypaper-brain/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())["data"]
        return [t["name"] for t in data.get("tags", [])]
    except Exception:
        return []


def keep(path) -> dict:
    """Register a wallpaper as kept. Returns the updated prefs."""
    path = Path(path).expanduser().resolve()
    wid = wid_from(path)
    prefs = load_prefs()
    if wid in prefs["kept"]:
        return prefs
    is_local = wid.startswith("local_")
    tags = [] if is_local else fetch_tags(wid)
    prefs["kept"][wid] = {
        "path": str(path),
        "tags": tags,
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if not is_local:
        for t in tags:
            prefs["tag_weights"][t] = prefs["tag_weights"].get(t, 0) + 1.0
        prefs["tag_count"] = sum(prefs["tag_weights"].values())
    prefs["discarded"].pop(wid, None)
    save_prefs(prefs)
    return prefs


def discard(path) -> dict:
    """Register a wallpaper as discarded. Returns the updated prefs."""
    path_obj = Path(path).expanduser().resolve()
    wid = wid_from(path_obj)
    if not wid:
        return load_prefs()
    prefs = load_prefs()
    prefs["discarded"][wid] = {
        "path": str(path_obj),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if wid in prefs["kept"]:
        for t in prefs["kept"][wid].get("tags", []):
            prefs["tag_weights"][t] = prefs["tag_weights"].get(t, 1.0) - 0.5
            if prefs["tag_weights"].get(t, 0) <= 0:
                prefs["tag_weights"].pop(t, None)
        del prefs["kept"][wid]
    save_prefs(prefs)
    return prefs


def forget(path) -> dict:
    """Remove a wallpaper from both kept and discarded. Returns updated prefs."""
    wid = wid_from(path)
    if not wid:
        return load_prefs()
    prefs = load_prefs()
    prefs["kept"].pop(wid, None)
    prefs["discarded"].pop(wid, None)
    save_prefs(prefs)
    return prefs


def get_status(wid: str) -> str | None:
    """Return 'kept', 'discarded', or None."""
    prefs = load_prefs()
    if wid in prefs.get("kept", {}):
        return "kept"
    if wid in prefs.get("discarded", {}):
        return "discarded"
    return None


def get_status_for_path(path) -> str | None:
    return get_status(wid_from(path))


def get_stats() -> dict:
    """Return brain stats as a dict."""
    prefs = load_prefs()
    top_tags = sorted(prefs["tag_weights"].items(), key=lambda x: -x[1])[:10]
    total = sum(1 for _ in LIBRARY_DIR.iterdir()) if LIBRARY_DIR.exists() else 0
    return {
        "total_on_disk": total,
        "kept_count": len(prefs["kept"]),
        "discarded_count": len(prefs["discarded"]),
        "tag_count": prefs["tag_count"],
        "top_tags": [{"tag": t, "weight": w} for t, w in top_tags],
        "last_cleanup": prefs.get("last_cleanup", ""),
        "last_recommend": prefs.get("last_recommend", ""),
    }
