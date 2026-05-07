# Cultivation World Wiki Tool

This helper builds a local static wiki from the game's real configuration and
registered Python classes. It is intended for quick developer/design lookup.

## Run

```powershell
python tools/wiki/serve.py
```

The script regenerates `tools/wiki/dist` only when the source config, code,
locales, static wiki files, or referenced assets have changed. It then serves
the generated folder and opens:

```text
http://127.0.0.1:8765
```

You can pass `--host`, `--port`, `--force`, `--no-open`, or `--out` if needed.

## Data Sources

- Languages: `static/locales/registry.json`
- World info and static content: `static/game_configs/*.csv`
- Actions: `src.classes.action.registry.ActionRegistry`
- Static game objects: the existing Python registries such as personas, sects,
  races, techniques, weapons, auxiliaries, elixirs, resources and regions.
- The generated site also adds category themes, global search, relationship
  chips, and completeness warnings for faster browsing.
