"""Flask web server for the Windows version of Waypaper.

Provides a REST API for browsing Wallhaven, managing a local library,
and changing the Windows wallpaper.

Logs errors to %APPDATA%/waypaper/server.log on Windows for debugging.
"""

import io
import logging
import os
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from waypaper import wallhaven, brain
from waypaper.brain import LIBRARY_DIR

app = Flask(__name__, static_folder=None)

TEMP_DIR = Path.home() / ".cache" / "waypaper" / "temp"

if os.name == "nt":
    LOG_DIR = Path(os.environ.get("APPDATA", "")) / "waypaper"
else:
    LOG_DIR = Path.home() / ".config" / "waypaper"

LOG_PATH = LOG_DIR / "server.log"


# ── Logging ───────────────────────────────────────────────────────────

def _setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        force=True,
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.info("=== Waypaper server starting ===")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")


def _log_error(msg: str, exc: Exception | None = None):
    if exc:
        logging.error(f"{msg}: {exc}", exc_info=True)
    else:
        logging.error(msg)


# ── Static files path ─────────────────────────────────────────────────

def _static_dir() -> Path:
    """Return path to static files, works in dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p = Path(sys._MEIPASS) / "waypaper" / "static"
        logging.info(f"Bundle mode, static dir: {p}")
        return p
    p = Path(__file__).parent / "static"
    logging.info(f"Dev mode, static dir: {p}")
    return p


# ── Helpers ──────────────────────────────────────────────────────────

def _library_files():
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        files.extend(sorted(LIBRARY_DIR.glob(ext)))
    return files


def _item_from_api(wallhaven_item) -> dict:
    return {
        "id": wallhaven_item.id,
        "thumb_url": wallhaven_item.thumb_url,
        "full_url": wallhaven_item.full_url,
        "resolution": wallhaven_item.resolution,
        "tags": wallhaven_item.tags,
    }


def _ext_from_url(url: str) -> str:
    return url.rsplit(".", 1)[-1].split("?")[0].split("#")[0] if "." in url else "jpg"


def _library_item_dict(f: Path) -> dict:
    name = f.stem
    wid = name[3:] if name.startswith("wh-") else name
    return {
        "id": wid,
        "name": name,
        "path": str(f),
        "status": brain.get_status(wid),
    }


FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Waypaper</title></head>
<body style="background:#1a1b1e;color:#c1c2c5;font:14px sans-serif;padding:40px;text-align:center">
<h1>Waypaper</h1>
<p style="color:#e03131">Static files not found. This is a packaging bug.</p>
<pre style="text-align:left;background:#25262b;padding:16px;border-radius:8px;max-width:600px;margin:20px auto">{}</pre>
</body></html>"""


# ── Routes ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    static = _static_dir()
    index_path = static / "index.html"
    if not index_path.exists():
        _log_error(f"index.html not found at {index_path}")
        return FALLBACK_HTML.replace("{}", f"Expected: {index_path}"), 500
    return send_from_directory(str(static), "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    static = _static_dir()
    file_path = static / filename
    if not file_path.exists():
        _log_error(f"static file not found: {file_path}")
        return jsonify({"error": "not found"}), 404
    return send_from_directory(str(static), filename)


@app.route("/api/search")
def api_search():
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
        _log_error("search failed", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/thumb/<wid>")
def api_thumb(wid):
    thumb_url = request.args.get("url", "")
    if not thumb_url:
        return jsonify({"error": "no thumb_url"}), 400
    try:
        result = wallhaven.fetch_thumbnail(thumb_url)
        if result is None:
            return jsonify({"error": "fetch failed"}), 502
        if isinstance(result, bytes):
            return send_file(io.BytesIO(result), mimetype="image/jpeg")
        buf = io.BytesIO()
        result.save_to_callback(buf.write, "jpeg", {"quality": "85"})
        buf.seek(0)
        return send_file(buf, mimetype="image/jpeg")
    except Exception as e:
        _log_error(f"thumb failed for {wid}", e)
        return jsonify({"error": str(e)}), 502


@app.route("/api/thumb_local/<name>")
def api_thumb_local(name):
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = LIBRARY_DIR / f"{name}.{ext}"
        if p.exists():
            return send_file(str(p), mimetype=f"image/{ext}")
    return jsonify({"error": "not found"}), 404


@app.route("/api/temp/<name>")
def api_temp(name):
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = TEMP_DIR / f"{name}.{ext}"
        if p.exists():
            return send_file(str(p), mimetype=f"image/{ext}")
    return jsonify({"error": "not found"}), 404


@app.route("/api/library")
def api_library():
    try:
        files = _library_files()
        return jsonify({
            "items": [_library_item_dict(f) for f in files],
            "count": len(files),
        })
    except Exception as e:
        _log_error("library listing failed", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/status")
def api_status():
    wid = request.args.get("id", "")
    if wid:
        return jsonify({"status": brain.get_status(wid)})
    try:
        return jsonify(brain.get_stats())
    except Exception as e:
        _log_error("status failed", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<wid>", methods=["POST"])
def api_download(wid):
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url required"}), 400
    try:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        ext = _ext_from_url(full_url)
        dest = TEMP_DIR / f"wh-{wid}.{ext}"
        result = wallhaven.download_full(full_url, dest)
        if result:
            return jsonify({"path": str(dest)})
        return jsonify({"error": "download failed"}), 502
    except Exception as e:
        _log_error(f"download failed for {wid}", e)
        return jsonify({"error": str(e)}), 502


@app.route("/api/set/<wid>", methods=["POST"])
def api_set(wid):
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url required"}), 400
    try:
        LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        ext = _ext_from_url(full_url)
        lib_path = LIBRARY_DIR / f"wh-{wid}.{ext}"
        if not lib_path.exists():
            result = wallhaven.download_full(full_url, lib_path)
            if not result:
                return jsonify({"error": "download failed"}), 502

        from waypaper.changer_windows import set_wallpaper
        ok = set_wallpaper(str(lib_path))
        if ok:
            brain.keep(str(lib_path))
            return jsonify({"ok": True, "path": str(lib_path)})
        return jsonify({"error": "set wallpaper failed"}), 500
    except Exception as e:
        _log_error(f"set failed for {wid}", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/save/<wid>", methods=["POST"])
def api_save(wid):
    full_url = request.json.get("full_url", "") if request.is_json else ""
    if not full_url:
        return jsonify({"error": "full_url required"}), 400
    try:
        LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        ext = _ext_from_url(full_url)
        dest = LIBRARY_DIR / f"wh-{wid}.{ext}"
        if not dest.exists():
            result = wallhaven.download_full(full_url, dest)
            if not result:
                return jsonify({"error": "download failed"}), 502
        brain.keep(str(dest))
        return jsonify({"ok": True, "path": str(dest)})
    except Exception as e:
        _log_error(f"save failed for {wid}", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/<wid>", methods=["DELETE"])
def api_library_delete(wid):
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
    path = request.json.get("path", "") if request.is_json else ""
    for ext in ("jpg", "jpeg", "png", "bmp"):
        p = Path(path) if path else (LIBRARY_DIR / f"wh-{wid}.{ext}")
        if p.exists():
            brain.keep(str(p))
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@app.route("/api/health")
def api_health():
    return jsonify({"ok": True, "version": "2.8"})


# ── Server ───────────────────────────────────────────────────────────

def start_server(host="127.0.0.1", port=5000, open_browser=True):
    _setup_logging()

    # Try ports 5000–5010 if the default is busy
    for attempt_port in range(port, port + 11):
        try:
            _try_start(host, attempt_port, open_browser)
            return  # _try_start is blocking, only returns on success
        except OSError as e:
            if attempt_port < port + 10:
                logging.warning(f"Port {attempt_port} busy, trying {attempt_port + 1}")
                continue
            _log_error(f"all ports {port}-{attempt_port} busy", e)
            print(f"ERROR: Ports {port}-{attempt_port} are all in use.")
            print(f"Check {LOG_PATH} for details.")
            raise


def _try_start(host, port, open_browser):
    """Attempt to start the server on the given port."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    if open_browser:
        def _open():
            try:
                webbrowser.open(f"http://{host}:{port}")
            except Exception as e:
                logging.warning(f"Could not open browser: {e}")
        threading.Timer(1.5, _open).start()

    # Log static dir state
    static = _static_dir()
    logging.info(f"Static dir exists: {static.exists()}")
    if static.exists():
        for f in static.iterdir():
            logging.info(f"  static file: {f.name}")

    print(f"Waypaper running at http://{host}:{port}")
    print(f"Logs: {LOG_PATH}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    start_server()
