import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_new_style_generic_rank_claims_are_consistent():
    manifest = json.loads((ROOT / "plugin.json").read_text())
    assert manifest["version"] == "0.1.3"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["provenance"]["arxiv"] == "2609.01789v1"
    assert manifest["provenance"]["doi"] == "10.48550/arXiv.2609.01789"
    expected = {"odd": 2, "even": 1}
    for variant in manifest["variants"]:
        rank = expected[variant["id"]]
        assert variant["generic_rank"] == rank
        assert variant["historical_generic_rank_lower"] == rank
        assert variant["verified_generic_rank_lower"] == rank
        assert variant["generic_rank_claim_state"] == "generic_lower_bound_verified"
