import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_manifest_exposes_exactly_the_six_dmt_selected_triads():
    manifest=json.loads((ROOT/"plugin.json").read_text())
    assert manifest["id"]=="dmt_triad_rank4"
    assert manifest["name"]=="DMT Triad Family"
    assert manifest["version"]=="0.1.3"
    assert manifest["default_variant"]=="cef"
    assert manifest["minimum_rank_hunter_version"]=="0.9.2"
    variants=manifest["variants"]
    assert [v["id"] for v in variants]==["ace","acf","bde","bdf","bef","cef"]
    for variant in variants:
        assert variant["generic_rank"]==4
        assert variant["historical_generic_rank_lower"]==4
        assert variant["verified_generic_rank_lower"]==4
        assert variant["generic_rank_claim_state"]=="generic_lower_bound_verified"
        assert variant["validation_parameter"]=="12/5"

def test_manifest_provenance_names_paper_and_source_repository():
    manifest=json.loads((ROOT/"plugin.json").read_text())
    provenance=manifest["provenance"]
    assert provenance["paper_id"]=="DMT-001"
    assert provenance["source_repository"]=="crhillresearch/dmt-rank-jumps"
    assert "REA CURVE2" in provenance["aliases"]
    assert "Triad Family" in provenance["aliases"]
