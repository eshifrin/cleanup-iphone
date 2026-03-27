import json
from pathlib import Path

from src.layout_fixture import icon_state_to_fixture, write_fixture_file


def test_icon_state_to_fixture_handles_apps_and_folders_and_overflow():
    icon_state = [
        [
            {"displayName": "Phone", "bundleIdentifier": "com.apple.mobilephone"},
            {"displayName": "Messages", "bundleIdentifier": "com.apple.MobileSMS"},
            {"displayName": "Camera", "bundleIdentifier": "com.apple.camera"},
            {"displayName": "Music", "bundleIdentifier": "com.apple.Music"},
            {"displayName": "Extra Dock App", "bundleIdentifier": "com.example.extra"},
        ],
        [
            {"displayName": "Notion", "bundleIdentifier": "notion.id"},
            {
                "displayName": "LLM",
                "iconLists": [
                    [
                        {"displayName": "ChatGPT", "bundleIdentifier": "com.openai.chatgpt"},
                        {"displayName": "Claude", "bundleIdentifier": "com.anthropic.claude"},
                    ],
                    [{"displayName": "Gemini", "bundleIdentifier": "com.google.gemini"}],
                ],
            },
        ],
    ]

    fixture = icon_state_to_fixture(icon_state, generated_at="2026-03-27T00:00:00+00:00")

    assert fixture["meta"]["pageCapacity"] == 24
    assert fixture["pages"][0]["id"] == "dock"
    assert fixture["pages"][0]["overflowCount"] == 1
    assert len(fixture["pages"][0]["slots"]) == 4

    llm_folder = fixture["pages"][1]["slots"][1]["item"]
    assert llm_folder["type"] == "folder"
    assert llm_folder["name"] == "LLM"
    assert llm_folder["appCount"] == 3
    assert [app["name"] for app in llm_folder["apps"]] == ["ChatGPT", "Claude", "Gemini"]


def test_write_fixture_file_writes_json(tmp_path: Path):
    fixture = {"meta": {"generatedAt": "fixed"}, "pages": []}
    output = tmp_path / "fixtures" / "out.json"

    result = write_fixture_file(fixture, output)

    assert result == output
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == fixture
