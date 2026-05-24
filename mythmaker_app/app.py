from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import __version__
from .engine import generate_scene
from . import storage


ROOT = storage.repo_root()
STATIC_DIR = ROOT / "mythmaker_app" / "static"
TEMPLATE_DIR = ROOT / "mythmaker_app" / "templates"


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


class MythMakerHandler(BaseHTTPRequestHandler):
    server_version = "MythMaker/0.1"

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stdout.write("[mythmaker] " + fmt % args + "\n")

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: object, status: int = 200) -> None:
        self._send(status, _json_bytes(payload))

    def _read_json(self) -> dict:
        length = int(self.headers.get("content-length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._json({"ok": False, "error": "File not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, path.read_bytes(), content_type)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == "/":
                self._send_file(TEMPLATE_DIR / "index.html")
            elif path == "/api/state":
                self._json({"ok": True, "state": storage.load_state()})
            elif path == "/api/favourites":
                self._json({"ok": True, "favourites": storage.list_favourites()})
            elif path == "/api/doctor":
                self._json({"ok": True, "version": __version__, "python": sys.version.split()[0], "doctor": storage.doctor()})
            elif path.startswith("/static/"):
                self._send_file(_safe_static_path(path))
            else:
                self._json({"ok": False, "error": "Unknown route"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self._json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            payload = self._read_json()
            if path == "/api/state":
                if payload.get("reset"):
                    state = storage.reset_state()
                else:
                    state = storage.save_state(payload.get("state") or payload)
                self._json({"ok": True, "state": state})
            elif path == "/api/generate":
                state = storage.load_state()
                scene = generate_scene(state, payload)
                self._json({"ok": True, "scene": scene})
            elif path == "/api/favourites":
                scene = payload.get("scene") or {}
                if not isinstance(scene, dict) or not scene.get("script"):
                    self._json({"ok": False, "error": "No scene supplied"}, HTTPStatus.BAD_REQUEST)
                    return
                item = storage.save_favourite(scene)
                self._json({"ok": True, "favourite": item, "favourites": storage.list_favourites()})
            elif path == "/api/export":
                scene = payload.get("scene") or {}
                if not isinstance(scene, dict) or not scene.get("script"):
                    self._json({"ok": False, "error": "No scene supplied"}, HTTPStatus.BAD_REQUEST)
                    return
                result = storage.export_scene(scene, str(payload.get("format") or "txt"))
                self._json({"ok": True, "export": result})
            else:
                self._json({"ok": False, "error": "Unknown route"}, HTTPStatus.NOT_FOUND)
        except json.JSONDecodeError:
            self._json({"ok": False, "error": "Invalid JSON"}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self._json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def _safe_static_path(path: str) -> Path:
    requested = (STATIC_DIR / path.removeprefix("/static/")).resolve()
    root = STATIC_DIR.resolve()
    if root not in requested.parents and requested != root:
        return STATIC_DIR / "__missing__"
    return requested


def run(host: str = "127.0.0.1", port: int = 0, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), MythMakerHandler)
    actual_port = server.server_address[1]
    url = f"http://{host}:{actual_port}"
    print(f"MythMaker is running at {url}", flush=True)
    print("Press Ctrl+C in this window to stop it.", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMythMaker stopped.")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the local MythMaker app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true", help="Start without opening the browser.")
    parser.add_argument("--doctor", action="store_true", help="Print a local health check and exit.")
    args = parser.parse_args(argv)

    if args.doctor:
        print(json.dumps({"version": __version__, "python": sys.version.split()[0], "doctor": storage.doctor()}, indent=2))
        return

    run(args.host, args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
