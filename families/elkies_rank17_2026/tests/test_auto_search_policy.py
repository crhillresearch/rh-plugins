import json
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


def test_elkies_rank17_auto_search_policy_and_section_bundle():
    manifest = json.loads((HERE / "plugin.json").read_text(encoding="utf-8"))
    family = json.loads((HERE / "family.json").read_text(encoding="utf-8"))

    assert manifest["version"] == "1.3.1"
    assert manifest["generic_rank"] == 17
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert len(family["sections"]) == 17

    policy = manifest["auto_search"]
    assert policy["target_rank"] == 31
    assert policy["integral_minimal_until_rank"] == 25
    assert policy["baseline_certificate_timeout"] >= 120
    assert policy["exact_candidates"] >= 17
    assert "not a historical" in policy["strategy_note"].lower()
