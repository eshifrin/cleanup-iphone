# cleanup-iphone

Use this if your iPhone is a mess.

Best used with an agentic coding tool (ccode, codex, or Cursor). You can ask the agent to:

- see a clear list of installed apps and folders (`summarize --verbose`)
- download backup files of your current layout (`backup`)
- delete a subset from your current layout plan before applying changes
- suggest ideas for how to rearrange apps
- group apps logically into folders (just ask, then apply with `create-folder` / `move-app`)


Scripted iPhone home screen cleanup using USB + SpringBoard APIs.

This repo is meant to be practical:
- back up your layout safely,
- reorganize apps and folders,
- repack folders to remove odd spacing,
- restore instantly if you do not like the result.

## What This Uses

1. `libimobiledevice` (installed with Homebrew)  
   - Provides the low-level iPhone connection stack over USB.
2. `pymobiledevice3` (installed with pip)  
   - Python client that talks to SpringBoard (`get_icon_state` / `set_icon_state`).

See `docs/HOW_IT_WORKS.md` for technical detail.

## Quick Start

### 1) Install tools
```bash
brew install libimobiledevice
pip3 install -r requirements.txt
```

### 2) Plug iPhone in
- USB cable (not wireless)
- iPhone unlocked
- "Trust This Computer" accepted

### 3) Back up first (always)
```bash
python3 src/cleanup_iphone.py backup
```

### 4) Inspect current layout
```bash
python3 src/cleanup_iphone.py summarize --verbose
```

### 5) Make changes (dry run first)
```bash
python3 src/cleanup_iphone.py move-app --app "Notion" --page 2 --dry-run
python3 src/cleanup_iphone.py move-app --app "Notion" --page 2
```

### 6) Repack folders to remove weird spacing
```bash
python3 src/cleanup_iphone.py repack --dry-run
python3 src/cleanup_iphone.py repack
```

### 7) Restore if needed
```bash
python3 src/cleanup_iphone.py restore artifacts/backups/icon_layout_backup_YYYYMMDD_HHMMSS.plist
```

## Common Workflows

Create folder and move apps into it:
```bash
python3 src/cleanup_iphone.py create-folder \
  --name "LLM" \
  --page 1 \
  --apps "Claude" "ChatGPT" "Gemini" "Perplexity" "NotebookLM" \
  --dry-run
```

Then apply:
```bash
python3 src/cleanup_iphone.py create-folder \
  --name "LLM" \
  --page 1 \
  --apps "Claude" "ChatGPT" "Gemini" "Perplexity" "NotebookLM"
```

Move app into an existing folder:
```bash
python3 src/cleanup_iphone.py move-app --app "Find My" --page 1 --folder "Utilities"
```

More examples: `docs/PLAYBOOK.md`.
