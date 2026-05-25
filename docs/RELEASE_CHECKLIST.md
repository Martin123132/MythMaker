# MythMaker Release Checklist

Use this before publishing a public GitHub release.

## Local Checks

```powershell
python -m unittest discover -s tests
python -m compileall mythmaker_app tests scripts
python scripts\sample_scenes.py --demo --count 10
python -m mythmaker_app.app --doctor
```

## Fresh User Smoke Test

```powershell
$env:MYTHMAKER_HOME = "$env:TEMP\MythMakerFreshSmoke"
python -m mythmaker_app.app --no-open --port 0
```

In the browser:

1. Press `Generate Scene`.
2. Press `Regenerate Same Seed`.
3. Save a favourite.
4. Export TXT.
5. Export HTML.
6. Reset Bottom House.

Close the terminal with `Ctrl+C`, then remove the temporary smoke folder.

## Release ZIP

```powershell
powershell -ExecutionPolicy Bypass -File scripts\make_release_zip.ps1
```

Check the ZIP contains:

- `START_MythMaker_WINDOWS.bat`
- `README.md`
- `mythmaker_app\`
- `scripts\`
- `docs\`
- `tests\`

Check the ZIP does not contain:

- `.git\`
- `__pycache__\`
- `.pytest_cache\`
- local `%LOCALAPPDATA%\MythMaker` data

## GitHub Release

1. Push `main`.
2. Tag `v0.1.0`.
3. Upload `dist\MythMaker-v0.1.0.zip`.
4. Use release notes that say:
   - local-only,
   - no API keys,
   - Python 3.10+ required,
   - unzip, double-click, press `Generate Scene`.
