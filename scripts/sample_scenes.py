from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mythmaker_app.engine import MODES, generate_scene  # noqa: E402
from mythmaker_app.storage import load_default_state, load_state  # noqa: E402


DEMO_RUNS = [
    (101, "Bottom House", 72, 4),
    (202, "Therapy Under The Stairs", 74, 4),
    (303, "Five-a-Side", 70, 4),
    (404, "Cult Drift", 78, 5),
    (505, "Collision", 66, 4),
    (606, "Bottom House", 88, 5),
    (707, "Therapy Under The Stairs", 92, 3),
    (808, "Five-a-Side", 82, 5),
    (909, "Cult Drift", 60, 4),
    (1001, "Collision", 95, 5),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic MythMaker scenes for tuning.")
    parser.add_argument("--count", type=int, default=10, help="Number of scenes to generate.")
    parser.add_argument("--mode", choices=MODES, default="Random", help="Mode to use for non-demo runs.")
    parser.add_argument("--weirdness", type=int, default=72, help="Weirdness for non-demo runs.")
    parser.add_argument("--cast-size", type=int, default=4, help="Cast size for non-demo runs.")
    parser.add_argument("--start-seed", type=int, default=101, help="First seed for non-demo runs.")
    parser.add_argument("--demo", action="store_true", help="Use the curated demo seed set.")
    parser.add_argument("--user-state", action="store_true", help="Use saved local seed bank instead of built-in defaults.")
    parser.add_argument("--output-dir", type=Path, help="Write each scene as a TXT file in this directory.")
    args = parser.parse_args(argv)

    state = load_state() if args.user_state else load_default_state()
    requests = list(_scene_requests(args))
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for index, (seed, mode, weirdness, cast_size) in enumerate(requests, start=1):
        scene = generate_scene(
            state,
            {"seed": seed, "mode": mode, "weirdness": weirdness, "cast_size": cast_size},
        )
        text = _scene_text(scene)
        if args.output_dir:
            filename = f"{index:02d}-{_slugify(mode)}-seed-{seed}.txt"
            (args.output_dir / filename).write_text(text, encoding="utf-8")
        else:
            print("=" * 78)
            print(text)
    return 0


def _scene_requests(args: argparse.Namespace) -> Iterable[tuple[int, str, int, int]]:
    if args.demo:
        yield from DEMO_RUNS[: max(0, args.count)]
        return
    modes = MODES[1:] if args.mode == "Random" else [args.mode]
    for index in range(max(0, args.count)):
        mode = modes[index % len(modes)]
        seed = args.start_seed + (index * 101)
        weirdness = max(0, min(100, args.weirdness + ((index % 5) - 2) * 4))
        cast_size = max(2, min(5, args.cast_size + ((index % 3) - 1)))
        yield seed, mode, weirdness, cast_size


def _scene_text(scene: dict) -> str:
    return (
        f"Seed: {scene['seed']} | Mode: {scene['mode']} | "
        f"Weirdness: {scene['weirdness']} | Cast Size: {scene['cast_size']}\n\n"
        f"{scene['script']}\n"
    )


def _slugify(value: str) -> str:
    return "-".join(part for part in value.lower().replace("/", " ").split() if part)


if __name__ == "__main__":
    raise SystemExit(main())
