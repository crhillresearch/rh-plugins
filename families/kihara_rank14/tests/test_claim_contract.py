import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_separates_historical_from_operational_rank():
    manifest = json.loads((ROOT / "plugin.json").read_text())
    assert manifest["version"] == "1.2.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["historical_generic_rank_lower"] == 14
    assert manifest["verified_generic_rank_lower"] == 14
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert "generic_rank" not in manifest


def test_workers_do_not_write_unconditional_rank14_claims():
    for name in ("native_search.py", "chart_search.py"):
        text = (ROOT / name).read_text()
        assert "generic_lower=14" not in text
        assert '"generic_rank": 14' not in text
        assert "certify_specialized_sections" in text
