import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_manifest_filesystem_paths_are_plain():
    data = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert data["version"] == "1.2.4"
    assert "\\_" not in data.get("search_adapter", "")
    for variant in data["variants"]:
        path = variant["family"]["file"]
        assert "\\_" not in path
        assert (ROOT / path).exists(), path
