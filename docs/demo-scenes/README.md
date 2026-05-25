# MythMaker Demo Scenes

These scenes are generated from fixed seeds so release testing has something
repeatable to inspect.

Regenerate them from the repo root:

```powershell
python scripts\sample_scenes.py --demo --count 10 --output-dir docs\demo-scenes
```

Each file records the seed, mode, weirdness, and cast size used for that scene.
The app itself still generates fresh scenes normally.
