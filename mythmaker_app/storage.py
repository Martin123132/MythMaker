from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import time
from typing import Any

from .engine import scene_to_html, scene_to_text


APP_NAME = "MythMaker"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def app_data_dir() -> Path:
    override = os.getenv("MYTHMAKER_HOME")
    if override:
        root = Path(override).expanduser()
    elif os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    else:
        root = Path.home() / ".local" / "share" / "mythmaker"
    root.mkdir(parents=True, exist_ok=True)
    return root


def exports_dir() -> Path:
    path = app_data_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_state_path() -> Path:
    return repo_root() / "mythmaker_app" / "seeds" / "bottom_house.json"


def user_state_path() -> Path:
    return app_data_dir() / "world.json"


def favourites_path() -> Path:
    return app_data_dir() / "favourites.json"


def load_default_state() -> dict[str, Any]:
    return _read_json(default_state_path(), fallback={})


def load_state() -> dict[str, Any]:
    path = user_state_path()
    if not path.exists():
        state = load_default_state()
        save_state(state)
        return state
    state = _read_json(path, fallback=None)
    if not isinstance(state, dict) or not state.get("characters"):
        broken = path.with_suffix(f".broken-{int(time.time())}.json")
        try:
            shutil.copy2(path, broken)
        except OSError:
            pass
        state = load_default_state()
        save_state(state)
    return state


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_state(state)
    _write_json(user_state_path(), normalized)
    return normalized


def reset_state() -> dict[str, Any]:
    state = load_default_state()
    save_state(state)
    return state


def list_favourites() -> list[dict[str, Any]]:
    data = _read_json(favourites_path(), fallback=[])
    return data if isinstance(data, list) else []


def save_favourite(scene: dict[str, Any]) -> dict[str, Any]:
    favourites = list_favourites()
    item = {
        "id": f"fav-{int(time.time() * 1000)}",
        "title": str(scene.get("title") or "Untitled Myth"),
        "seed": scene.get("seed"),
        "mode": scene.get("mode"),
        "created_at": scene.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scene": scene,
    }
    favourites.insert(0, item)
    _write_json(favourites_path(), favourites[:100])
    return item


def export_scene(scene: dict[str, Any], export_format: str = "txt") -> dict[str, Any]:
    export_format = "html" if str(export_format).lower() == "html" else "txt"
    title = str(scene.get("title") or "mythmaker-scene")
    stem = _slugify(title)[:70] or "mythmaker-scene"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = exports_dir() / f"{stamp}-{stem}.{export_format}"
    content = scene_to_html(scene) if export_format == "html" else scene_to_text(scene)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "format": export_format, "title": title}


def doctor() -> dict[str, Any]:
    data_dir = app_data_dir()
    state = load_state()
    return {
        "python_data_dir": str(data_dir),
        "state_path": str(user_state_path()),
        "favourites_path": str(favourites_path()),
        "exports_dir": str(exports_dir()),
        "state_ok": bool(state.get("characters")),
        "character_count": len(state.get("characters", [])),
        "favourite_count": len(list_favourites()),
    }


def _normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    default = load_default_state()
    normalized = dict(default)
    if isinstance(state, dict):
        normalized.update(state)
    for key in ["characters", "places", "phrases", "relics", "rules"]:
        if not isinstance(normalized.get(key), list):
            normalized[key] = default.get(key, [])
    normalized["version"] = int(normalized.get("version") or 1)
    normalized["world_name"] = str(normalized.get("world_name") or "Bottom House")
    return normalized


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _slugify(value: str) -> str:
    value = value.lower()
    value = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-")
