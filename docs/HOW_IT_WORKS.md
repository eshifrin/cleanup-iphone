# How It Works

## Under The Hood

This toolkit uses two external pieces:

- `libimobiledevice`: the USB communication stack for iOS devices.
- `pymobiledevice3`: Python bindings/client for iOS services, including SpringBoard.

The relevant SpringBoard calls are:
- `get_icon_state`: read current home screen state.
- `set_icon_state`: write a new home screen state.

## Safety Model

Every mutating command should be run with `--dry-run` first.

When a mutating command is applied, the tool writes a pre-change backup plist to:
- `artifacts/backups/`

If something looks wrong, restore with:
```bash
python3 src/cleanup_iphone.py restore artifacts/backups/<backup-file>.plist
```

## Data Shape (Simplified)

The icon layout is a nested structure:
- top level: pages (`0` = dock, `1` = first home page)
- page entries: either
  - app dictionaries, or
  - folder dictionaries with `iconLists` arrays

Folder spacing weirdness usually comes from sparse `iconLists` pages after many moves.
The `repack` command compacts folder pages left-to-right.

## Why This Repo Exists

This is a practical automation log turned toolkit:
- first pass: ad-hoc scripts and LLM-guided moves
- second pass: grouped apps by intent (Read, LLM, Work, Money, etc.)
- final pass: repacked folder internals and cleaned dangling apps
