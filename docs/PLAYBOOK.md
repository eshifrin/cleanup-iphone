# Playbook

## Typical Session

1) Backup:
```bash
python3 src/cleanup_iphone.py backup
```

2) Inspect:
```bash
python3 src/cleanup_iphone.py summarize --verbose
```

3) Plan one small change:
- move one app
- create one folder
- repack

4) Dry-run first:
```bash
python3 src/cleanup_iphone.py move-app --app "Notion" --page 2 --dry-run
```

5) Apply:
```bash
python3 src/cleanup_iphone.py move-app --app "Notion" --page 2
```

6) Repack after bigger edits:
```bash
python3 src/cleanup_iphone.py repack
```

## Example: Build a Read Folder

```bash
python3 src/cleanup_iphone.py create-folder \
  --name "Read" \
  --page 1 \
  --apps "Kindle" "Economist" "NYTimes" "FT" "WSJ" "Substack"
```

## Example: Group LLM Apps

```bash
python3 src/cleanup_iphone.py create-folder \
  --name "LLM" \
  --page 1 \
  --apps "Claude" "ChatGPT" "Gemini" "Perplexity" "NotebookLM"
```

## Example: Pull Utility Apps to Desktop

```bash
python3 src/cleanup_iphone.py move-app --app "Find My" --page 1
python3 src/cleanup_iphone.py move-app --app "Voice Memos" --page 1
```

## Recovery

List backups:
```bash
ls -1 artifacts/backups/*.plist
```

Restore:
```bash
python3 src/cleanup_iphone.py restore artifacts/backups/<backup-file>.plist
```
