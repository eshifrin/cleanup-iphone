#!/usr/bin/env python3
"""
Unified iPhone home screen layout toolkit.

Commands:
  - backup
  - restore
  - summarize
  - repack
  - move-app
  - create-folder
"""

import argparse
import asyncio
import json
import logging
import os
import plistlib
import sys
from datetime import datetime
from pathlib import Path

logging.getLogger("asyncio").setLevel(logging.CRITICAL)


def _run(coro):
    """Run coroutine while suppressing noisy asyncio teardown stderr."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, "w")
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr


def app_name(item):
    if not isinstance(item, dict):
        return "?"
    return item.get("displayName") or item.get("bundleIdentifier") or item.get("displayIdentifier") or "?"


def ensure_page(icon_state, index):
    while len(icon_state) <= index:
        icon_state.append([])
    if not isinstance(icon_state[index], list):
        icon_state[index] = []


def flatten_folder_apps(folder):
    apps = []
    icon_lists = folder.get("iconLists", [])
    if not isinstance(icon_lists, list):
        return apps
    for folder_page in icon_lists:
        if isinstance(folder_page, list):
            apps.extend([x for x in folder_page if isinstance(x, dict)])
    return apps


def repack_folder(folder, chunk_size=9):
    apps = flatten_folder_apps(folder)
    if not apps:
        folder["iconLists"] = [[]]
        return 0
    folder["iconLists"] = [apps[i : i + chunk_size] for i in range(0, len(apps), chunk_size)]
    return len(apps)


def find_folder(page, folder_name):
    for idx, item in enumerate(page):
        if isinstance(item, dict) and "iconLists" in item and item.get("displayName") == folder_name:
            return idx, item
    return None, None


def append_to_folder(folder, app):
    icon_lists = folder.get("iconLists")
    if not isinstance(icon_lists, list) or len(icon_lists) == 0:
        folder["iconLists"] = [[app]]
        return
    if not isinstance(icon_lists[0], list):
        icon_lists[0] = []
    icon_lists[0].append(app)


def pop_app_by_name(icon_state, target_name, include_home=True):
    for page_idx, page in enumerate(icon_state):
        if not include_home and page_idx == 1:
            continue
        if not isinstance(page, list):
            continue
        for item_idx in range(len(page) - 1, -1, -1):
            item = page[item_idx]
            if not isinstance(item, dict):
                continue

            # Top-level app
            if "iconLists" not in item and app_name(item) == target_name:
                return page.pop(item_idx), f"page {page_idx} item {item_idx}"

            # App inside folder
            if "iconLists" in item and isinstance(item["iconLists"], list):
                for fp_idx, fp in enumerate(item["iconLists"]):
                    if not isinstance(fp, list):
                        continue
                    for fi_idx in range(len(fp) - 1, -1, -1):
                        child = fp[fi_idx]
                        if isinstance(child, dict) and app_name(child) == target_name:
                            return fp.pop(fi_idx), (
                                f"page {page_idx} folder '{app_name(item)}' "
                                f"page {fp_idx} item {fi_idx}"
                            )
    return None, None


def make_json_safe(obj):
    if isinstance(obj, bytes):
        return f"<{len(obj)} bytes>"
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(x) for x in obj]
    return obj


def list_apps_text(icon_state):
    lines = []

    def walk(node):
        if isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            if "iconLists" in node:
                lines.append("")
                lines.append(f"--- Folder: {node.get('displayName', 'Unnamed')} ---")
                walk(node["iconLists"])
            else:
                lines.append(app_name(node))

    walk(icon_state)
    return lines


class DeviceClient:
    def __init__(self):
        self.sbs = None

    async def connect(self):
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.services.springboard import SpringBoardServicesService

        lockdown = create_using_usbmux()
        if asyncio.iscoroutine(lockdown):
            lockdown = await lockdown
        sbs = SpringBoardServicesService(lockdown=lockdown)
        if asyncio.iscoroutine(sbs):
            sbs = await sbs
        self.sbs = sbs

    async def get_state(self):
        state = self.sbs.get_icon_state()
        if asyncio.iscoroutine(state):
            state = await state
        return state

    async def set_state(self, state):
        res = self.sbs.set_icon_state(state)
        if asyncio.iscoroutine(res):
            await res


def save_backup_files(base_dir, icon_state):
    base_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    plist_path = base_dir / f"icon_layout_backup_{ts}.plist"
    json_path = base_dir / f"icon_layout_backup_{ts}.json"
    txt_path = base_dir / f"apps_on_homescreen_{ts}.txt"

    with open(plist_path, "wb") as f:
        plistlib.dump(icon_state, f)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(make_json_safe(icon_state), f, indent=2)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Home Screen Apps\n")
        f.write(f"Backed up: {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n\n")
        for line in list_apps_text(icon_state):
            f.write(line + "\n")

    return plist_path, json_path, txt_path


def save_prechange_backup(base_dir, icon_state, prefix):
    base_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = base_dir / f"{prefix}_{ts}.plist"
    with open(path, "wb") as f:
        plistlib.dump(icon_state, f)
    return path


async def cmd_backup(args):
    client = DeviceClient()
    await client.connect()
    state = await client.get_state()
    plist_path, json_path, txt_path = save_backup_files(Path(args.output_dir), state)
    print(f"Saved: {plist_path}")
    print(f"Saved: {json_path}")
    print(f"Saved: {txt_path}")


async def cmd_restore(args):
    backup_path = Path(args.backup)
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        sys.exit(1)

    with open(backup_path, "rb") as f:
        state = plistlib.load(f)

    client = DeviceClient()
    await client.connect()

    if args.dry_run:
        print(f"[DRY RUN] Would restore from: {backup_path}")
        return

    await client.set_state(state)
    print(f"Restored layout from: {backup_path}")


async def cmd_summarize(args):
    client = DeviceClient()
    await client.connect()
    state = await client.get_state()

    for page_idx, page in enumerate(state):
        label = "Dock" if page_idx == 0 else f"Page {page_idx}"
        top, folders = 0, 0
        if isinstance(page, list):
            for item in page:
                if isinstance(item, dict) and "iconLists" in item:
                    folders += 1
                elif isinstance(item, dict):
                    top += 1
        print(f"{label}: {top + folders} items ({top} loose, {folders} folders)")

        if args.verbose and isinstance(page, list):
            for item in page:
                if isinstance(item, dict) and "iconLists" in item:
                    count = len(flatten_folder_apps(item))
                    print(f"  [Folder] {app_name(item)} ({count})")
                elif isinstance(item, dict):
                    print(f"  - {app_name(item)}")


async def cmd_repack(args):
    client = DeviceClient()
    await client.connect()
    state = await client.get_state()

    changed = 0
    for page_idx, page in enumerate(state):
        if not isinstance(page, list):
            continue
        for item in page:
            if isinstance(item, dict) and "iconLists" in item:
                before_pages = len(item.get("iconLists", [])) if isinstance(item.get("iconLists"), list) else 0
                repack_folder(item, chunk_size=args.chunk_size)
                after_pages = len(item.get("iconLists", []))
                if before_pages != after_pages:
                    changed += 1
                    print(f"Repacked '{app_name(item)}' on page {page_idx}: {before_pages} -> {after_pages} pages")

    if args.dry_run:
        print(f"[DRY RUN] Repacked folders. Changed page counts in {changed} folder(s).")
        return

    backup = save_prechange_backup(Path(args.output_dir), state, "pre_repack")
    await client.set_state(state)
    print(f"Applied repack. Backup: {backup}")


async def cmd_move_app(args):
    client = DeviceClient()
    await client.connect()
    state = await client.get_state()

    app, src = pop_app_by_name(state, args.app)
    if app is None:
        print(f"App not found: {args.app}")
        sys.exit(1)

    ensure_page(state, args.page)
    target_page = state[args.page]

    if args.folder:
        _, folder = find_folder(target_page, args.folder)
        if folder is None:
            folder = {"iconLists": [[]], "listType": "folder", "displayName": args.folder}
            target_page.append(folder)
            print(f"Created folder '{args.folder}' on page {args.page}")
        append_to_folder(folder, app)
        dest_desc = f"folder '{args.folder}' on page {args.page}"
    else:
        target_page.append(app)
        dest_desc = f"page {args.page}"

    print(f"Move: {args.app} from {src} -> {dest_desc}")

    if args.dry_run:
        print("[DRY RUN] No changes applied.")
        return

    backup = save_prechange_backup(Path(args.output_dir), state, "pre_move_app")
    await client.set_state(state)
    print(f"Applied move. Backup: {backup}")


async def cmd_create_folder(args):
    client = DeviceClient()
    await client.connect()
    state = await client.get_state()
    ensure_page(state, args.page)

    page = state[args.page]
    _, folder = find_folder(page, args.name)
    if folder is None:
        folder = {"iconLists": [[]], "listType": "folder", "displayName": args.name}
        page.append(folder)
        print(f"Created folder '{args.name}' on page {args.page}")
    else:
        print(f"Using existing folder '{args.name}' on page {args.page}")

    moved = 0
    for app_name_input in args.apps:
        app, src = pop_app_by_name(state, app_name_input)
        if app is None:
            print(f"Skip: {app_name_input} (not found)")
            continue
        append_to_folder(folder, app)
        moved += 1
        print(f"Move: {app_name_input} from {src} -> folder '{args.name}'")

    repack_folder(folder, chunk_size=9)

    if args.dry_run:
        print(f"[DRY RUN] Would move {moved} apps into '{args.name}'.")
        return

    backup = save_prechange_backup(Path(args.output_dir), state, "pre_create_folder")
    await client.set_state(state)
    print(f"Applied folder update. Backup: {backup}")


def build_parser():
    parser = argparse.ArgumentParser(description="iPhone home screen cleanup toolkit")
    parser.add_argument(
        "--output-dir",
        default="artifacts/backups",
        help="Directory for backups and generated files (default: artifacts/backups)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_backup = sub.add_parser("backup", help="Read layout from device and save backups")
    p_backup.set_defaults(func=cmd_backup)

    p_restore = sub.add_parser("restore", help="Restore layout from a plist backup")
    p_restore.add_argument("backup", help="Path to backup plist file")
    p_restore.add_argument("--dry-run", action="store_true", help="Preview only, do not apply")
    p_restore.set_defaults(func=cmd_restore)

    p_sum = sub.add_parser("summarize", help="Print page/folder summary from live device")
    p_sum.add_argument("--verbose", action="store_true", help="Show items and folder names")
    p_sum.set_defaults(func=cmd_summarize)

    p_repack = sub.add_parser("repack", help="Repack all folders to remove sparse pages")
    p_repack.add_argument("--chunk-size", type=int, default=9, help="Apps per folder page (default: 9)")
    p_repack.add_argument("--dry-run", action="store_true", help="Preview only, do not apply")
    p_repack.set_defaults(func=cmd_repack)

    p_move = sub.add_parser("move-app", help="Move one app to a page or folder")
    p_move.add_argument("--app", required=True, help="App display name (e.g., Notion)")
    p_move.add_argument("--page", type=int, required=True, help="Target page index (1 = first home page)")
    p_move.add_argument("--folder", help="Optional target folder name on that page")
    p_move.add_argument("--dry-run", action="store_true", help="Preview only, do not apply")
    p_move.set_defaults(func=cmd_move_app)

    p_folder = sub.add_parser("create-folder", help="Create/use folder and move apps into it")
    p_folder.add_argument("--name", required=True, help="Folder name")
    p_folder.add_argument("--page", type=int, required=True, help="Target page index")
    p_folder.add_argument("--apps", nargs="+", required=True, help="App display names to move")
    p_folder.add_argument("--dry-run", action="store_true", help="Preview only, do not apply")
    p_folder.set_defaults(func=cmd_create_folder)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    _run(args.func(args))


if __name__ == "__main__":
    main()
