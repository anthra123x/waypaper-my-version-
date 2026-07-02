"""Flask web server for the Windows version of Waypaper.

Provides a REST API for browsing Wallhaven, managing a local library,
and changing the Windows wallpaper.
"""

import io
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from waypaper import wallhaven, brain
from waypaper.brain import LIBRARY_DIR

app = Flask(__name__, static_folder=None)


def _static_dir() -> Path:
    """Return path to static files, works in dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / "waypaper" / "static"
    return Path(__file__).parent / "static"


TEMP_DIR = Path.home() / ".cache" / "waypaper" / "temp"


# ── Helpers ──────────────────────────────────────────────────────────

def _library_files():
    """Return sorted list of library wallpaper files."""
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        files.extend(sorted(LIBRARY_DIR.glob(ext)))
    return files


def _item_from_api(wallhaven_item) -> dict:
    """Convert a Wallhaven search result item to a JSON-safe dict."""
    return {
        "id": wallhaven_item.id,
        "thumb_url": wallhaven_item.thumb_url,
        "full_url": wallhaven_item.full_url,
        "resolution": wallhaven_item.resolution,
        "tags": wallhaven_item.tags,
    }


def _ext_from_url(url: str) -> str:
    """Extract file extension from a URL."""
    return url.rsplit(".", 1)[-1].split("?")[0].split("#")[0] if "." in url else "jpg"


def _library_item_dict(f: Path) -> dict:
    """Build a JSON-safe representation of a library file."""
    name = f.stem
    wid = name[3:] if name.startswith("wh-") else name
    return {
        "id": wid,
        "name": name,
        "path": str(f),
        "status": brain.get_status(wid),
    }


# ── Routes ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(_static_dir()), "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(_static_dir()), filename)


@app.route("/api/search")
def api_search():
    """Search Wallhaven API."""
    preset = request.args.get("preset", "random")
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    try:
        items, meta = wallhaven.search(preset, query, page)
        return jsonify({
            "items": [_item_from_api(i) for i in items],
            "page": meta.current,
            "last_page": meta.last,
            "total": meta.total,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/thumb/<wid>")
def api_thumb(wid):
    """Proxy a thumbnail from the Wallhaven CDN (used for search results)."""
    # The item's thumb_url is passed as ?url=.
    # The caller passes ?url= as a fallback for simplicity.
    thumb_url = request.args.get("url", "")
    if not thumb_url:
        return jsonify({"error": "no thumb_url provided"}), 400

    try:
        result = wallhaven.fetch_thumbnail(thumb_url)
        if result is None:
            return jsonify({"error": "failed to fetch thumbnail"}), 502
        # Handle both Pixbuf (Linux) and raw bytes (Windows)
        if isinstance(result, bytes):
            return send_file(io.BytesIO(result), mimetype="image/jpeg")
        buf = io.BytesIO()
        result.save_to_callback(buf.write, "jpeg", {"quality": "85"})
        buf.seek(0)
        return send_file(buf, mimetype="image/jpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/thumb_local/<name>")
def api_thumb_local(name):
    """Serve a local library file as a thumbnail."""
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = LIBRARY_DIR / f"{name}.{ext}"
        if p.exists():
            return send_file(str(p), mimetype=f"image/{ext}")
    return jsonify({"error": "not found"}), 404


@app.route("/api/temp/<name>")
def api_temp(name):
    """Serve a file from the temp cache directory (for previews)."""
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = TEMP_DIR / f"{name}.{ext}"
        if p.exists():
            return send_file(str(p), mimetype=f"image/{ext}")
    return jsonify({"error": "not found"}), 404


@app.route("/api/library")
def api_library():
    """List saved wallpapers in the library folder."""
    files = _library_files()
    return jsonify({
        "items": [_library_item_dict(f) for f in files],
        "count": len(files),
    })


@app.route("/api/status")
def api_status():
    """Brain status and stats.

    With ?id=xxx returns per-item status: {"status": "kept"|"discarded"|null}.
    Without ?id= returns aggregate stats.
    """
    wid = request.args.get("id", "")
    if wid:
        return jsonify({"status": brain.get_status(wid)})
    try:
        return jsonify(brain.get_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<wid>", methods=["POST"])
def api_download(wid):
    """Download a full-resolution wallpaper to temp, return local path."""
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url is required"}), 400

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    ext = _ext_from_url(full_url)
    dest = TEMP_DIR / f"wh-{wid}.{ext}"
    result = wallhaven.download_full(full_url, dest)
    if result:
        return jsonify({"path": str(dest)})
    return jsonify({"error": "download failed"}), 502


@app.route("/api/set/<wid>", methods=["POST"])
def api_set(wid):
    """Save to library then set as wallpaper."""
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url is required"}), 400

    # Save to library first (so brain records a permanent path)
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    ext = _ext_from_url(full_url)
    lib_path = LIBRARY_DIR / f"wh-{wid}.{ext}"
    if not lib_path.exists():
        result = wallhaven.download_full(full_url, lib_path)
        if not result:
            return jsonify({"error": "download failed"}), 502

    # Set wallpaper from library path
    try:
        from waypaper.changer_windows import set_wallpaper
        ok = set_wallpaper(str(lib_path))
        if ok:
            brain.keep(str(lib_path))
            return jsonify({"ok": True, "path": str(lib_path)})
        return jsonify({"error": "set_wallpaper failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save/<wid>", methods=["POST"])
def api_save(wid):
    """Download to library folder and register as kept."""
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url is required"}), 400

    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    ext = _ext_from_url(full_url)
    dest = LIBRARY_DIR / f"wh-{wid}.{ext}"

    if not dest.exists():
        result = wallhaven.download_full(full_url, dest)
        if not result:
            return jsonify({"error": "download failed"}), 502

    brain.keep(str(dest))
    return jsonify({"ok": True, "path": str(dest)})


@app.route("/api/library/<wid>", methods=["DELETE"])
def api_library_delete(wid):
    """Delete a library wallpaper from disk and discard in brain."""
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = LIBRARY_DIR / f"wh-{wid}.{ext}"
        if p.exists():
            brain.discard(str(p))
            try:
                p.unlink()
            except Exception:
                pass
            return jsonify({"ok": True, "deleted": str(p)})
    return jsonify({"error": "not found"}), 404


@app.route("/api/discard/<wid>", methods=["POST"])
def api_discard(wid):
    """Discard a library wallpaper (brain only, keep file)."""
    full_url = request.json.get("full_url", "") if request.is_json else ""
    path = request.json.get("path", "") if request.is_json else ""

    if path:
        brain.discard(str(path))
    elif full_url:
        ext = _ext_from_url(full_url)
        p = LIBRARY_DIR / f"wh-{wid}.{ext}"
        if p.exists():
            brain.discard(str(p))
        else:
            brain.discard(f"wh-{wid}.{ext if ext else 'jpg'}")
    else:
        brain.discard(f"wh-{wid}.jpg")
    return jsonify({"ok": True})


@app.route("/api/keep/<wid>", methods=["POST"])
def api_keep(wid):
    """Mark an existing library wallpaper as kept in brain."""
    path = request.json.get("path", "") if request.is_json else ""
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = Path(path) if path else (LIBRARY_DIR / f"wh-{wid}.{ext}")
        if p.exists():
            brain.keep(str(p))
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


# ── Server ───────────────────────────────────────────────────────────

def start_server(host="127.0.0.1", port=5000, open_browser=True):
    """Start the Flask server and optionally open the browser."""
    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    # Ensure directories exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🌐 Waypaper web UI at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    start_server()
