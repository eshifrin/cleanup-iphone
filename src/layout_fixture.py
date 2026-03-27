"""Utilities for turning icon state into UI fixtures."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

GRID_COLUMNS = 4
GRID_ROWS = 6
PAGE_CAPACITY = GRID_COLUMNS * GRID_ROWS
DOCK_CAPACITY = 4


def _display_name(item: dict) -> str:
    return item.get("displayName") or item.get("bundleIdentifier") or item.get("displayIdentifier") or "Unknown App"


def _slugify(value: str) -> str:
    lowered = value.lower()
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-") or "item"


def _normalize_app(item: dict, unique_suffix: str) -> dict:
    name = _display_name(item)
    bundle_id = item.get("bundleIdentifier") or item.get("displayIdentifier")
    app_id_source = bundle_id or name
    return {
        "id": f"app-{_slugify(app_id_source)}-{unique_suffix}",
        "type": "app",
        "name": name,
        "bundleId": bundle_id,
    }


def _flatten_folder_apps(folder: dict) -> list[dict]:
    apps = []
    icon_lists = folder.get("iconLists", [])
    if not isinstance(icon_lists, list):
        return apps
    for folder_page in icon_lists:
        if not isinstance(folder_page, list):
            continue
        for child in folder_page:
            if isinstance(child, dict):
                apps.append(child)
    return apps


def _normalize_item(item: object, page_index: int, item_index: int) -> dict | None:
    unique_suffix = f"{page_index}-{item_index}"
    if not isinstance(item, dict):
        return None
    if "iconLists" in item:
        folder_name = item.get("displayName") or "Unnamed Folder"
        children = [
            _normalize_app(child, f"{unique_suffix}-{child_idx}")
            for child_idx, child in enumerate(_flatten_folder_apps(item))
        ]
        return {
            "id": f"folder-{_slugify(folder_name)}-{unique_suffix}",
            "type": "folder",
            "name": folder_name,
            "appCount": len(children),
            "apps": children,
        }
    return _normalize_app(item, unique_suffix)


def _page_capacity(page_index: int) -> int:
    return DOCK_CAPACITY if page_index == 0 else PAGE_CAPACITY


def icon_state_to_fixture(icon_state: object, generated_at: str | None = None) -> dict:
    pages = []
    if generated_at is None:
        generated_at = datetime.now(tz=timezone.utc).isoformat()

    state_pages = icon_state if isinstance(icon_state, list) else []
    for page_index, page in enumerate(state_pages):
        capacity = _page_capacity(page_index)
        slots = [{"slotIndex": slot_index, "item": None} for slot_index in range(capacity)]
        overflow_count = 0

        if isinstance(page, list):
            for item_index, item in enumerate(page):
                if item_index >= capacity:
                    overflow_count += 1
                    continue
                slots[item_index]["item"] = _normalize_item(item, page_index, item_index)

        page_name = "Dock" if page_index == 0 else f"Page {page_index}"
        pages.append(
            {
                "id": "dock" if page_index == 0 else f"page-{page_index}",
                "name": page_name,
                "pageIndex": page_index,
                "capacity": capacity,
                "overflowCount": overflow_count,
                "slots": slots,
            }
        )

    return {
        "meta": {
            "generatedAt": generated_at,
            "grid": {"columns": GRID_COLUMNS, "rows": GRID_ROWS},
            "dockCapacity": DOCK_CAPACITY,
            "pageCapacity": PAGE_CAPACITY,
        },
        "pages": pages,
    }


def write_fixture_file(fixture: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(fixture, handle, indent=2)
        handle.write("\n")
    return output_path
