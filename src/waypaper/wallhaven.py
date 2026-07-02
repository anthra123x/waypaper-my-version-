"""Wallhaven API client — fetch wallpapers, thumbnails, and full-res downloads"""

import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf


API = "https://wallhaven.cc/api/v1"
UA = "waypaper-wallhaven/1.0"

CAT_PRESETS = {
    "random":   {"cats": "111", "purity": "100", "sorting": "random"},
    "anime":    {"cats": "010", "purity": "100", "sorting": "random"},
    "manga":    {"cats": "010", "purity": "100", "q": "manga panel", "sorting": "random"},
    "sketch":   {"cats": "111", "purity": "010", "sorting": "random"},
    "general":  {"cats": "100", "purity": "100", "sorting": "random"},
}


@dataclass
class WallpaperItem:
    id: str
    thumb_url: str
    full_url: str
    resolution: str
    tags: list[str]


@dataclass
class PageMeta:
    current: int = 1
    last: int = 1
    total: int = 0


_last_req = 0.0


def _request(url: str) -> dict:
    global _last_req
    elapsed = time.time() - _last_req
    if elapsed < 1.5:
        time.sleep(1.5 - elapsed)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        _last_req = time.time()
        return json.loads(resp.read().decode())


def search(preset: str, query: str = "", page: int = 1) -> tuple[list[WallpaperItem], PageMeta]:
    """Search Wallhaven by preset category with optional query text."""
    p = CAT_PRESETS.get(preset, CAT_PRESETS["random"])
    params = {
        "categories": p["cats"],
        "purity": p["purity"],
        "sorting": p["sorting"],
        "page": str(page),
    }
    if query:
        params["q"] = query
    elif p.get("q"):
        params["q"] = p["q"]

    url = f"{API}/search?{urllib.parse.urlencode(params)}"
    data = _request(url)

    meta = PageMeta(
        current=data.get("meta", {}).get("current_page", 1),
        last=data.get("meta", {}).get("last_page", 1),
        total=data.get("meta", {}).get("total", 0),
    )

    items = []
    for item in data.get("data", []):
        items.append(WallpaperItem(
            id=item.get("id", ""),
            thumb_url=item.get("thumbs", {}).get("small", ""),
            full_url=item.get("path", ""),
            resolution=item.get("resolution", ""),
            tags=[t.get("name", "") for t in item.get("tags", [])],
        ))

    return items, meta


def fetch_thumbnail(thumb_url: str) -> Optional[GdkPixbuf.Pixbuf]:
    """Download a thumbnail from the CDN and return a pixbuf (in memory, no disk)."""
    if not thumb_url:
        return None
    try:
        req = urllib.request.Request(thumb_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        loader = GdkPixbuf.PixbufLoader()
        loader.write(data)
        loader.close()
        return loader.get_pixbuf()
    except Exception:
        return None


def download_full(full_url: str, dest: Path) -> Optional[Path]:
    """Download full-resolution wallpaper to dest. Returns dest on success."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(full_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return dest
    except Exception:
        return None
