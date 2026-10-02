from __future__ import annotations

import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_matches_dujella_preprint_and_current_core():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "fibonacci_triples"
    assert manifest["name"] == "Fibonacci Triples"
    assert manifest["version"] == "0.1.3"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["default_variant"] == "odd"

    provenance = manifest["provenance"]
    assert provenance["arxiv"] == "2609.01789v1"
    assert provenance["doi"] == "10.48550/arXiv.2609.01789"
    assert provenance["submitted"] == "2026-09-01"
    assert "Theorem 5.1" in provenance["theorem_reference"]
    assert "Proposition 3.3" in provenance["theorem_reference"]

    by_id = {variant["id"]: variant for variant in manifest["variants"]}
    assert by_id["odd"]["generic_rank"] == 2
    assert by_id["odd"]["verified_generic_rank_lower"] == 2
    assert by_id["even"]["generic_rank"] == 1
    assert by_id["even"]["verified_generic_rank_lower"] == 1
    assert all(
        variant["generic_rank_claim_state"] == "generic_lower_bound_verified"
        for variant in manifest["variants"]
    )


def test_current_core_validates_both_parity_variants_and_adapter():
    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "0.1.3"
    assert result["default_variant"] == "odd"
    assert [variant["id"] for variant in result["variants"]] == ["odd", "even"]

    lower_bounds = {"odd": 2, "even": 1}
    for variant in result["variants"]:
        assert variant["validation_discriminant_nonzero"] is True
        certificate = variant["generic_rank_certificate"]
        assert certificate["verified"] is True
        assert certificate["lower_bound"] >= lower_bounds[variant["id"]]
        assert certificate["certificate_version"] == "fibonacci-triples-v0.1.3"

    assert result["adapter_contract"]["api_version"] == 1


def test_release_readme_is_portable_and_preserves_claim_boundary():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Rank Hunter **0.9.2**" in readme
    assert "Theorem 5.1" in readme
    assert "Proposition 3.3" in readme
    assert "generic rank **2**" in readme
    assert "generic rank **1**" in readme
    assert 'PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python' in readme

    assert "/home/" not in readme
    assert "/Users/" not in readme
    assert "miniforge3" not in readme
    assert "v0.8.7.1" not in readme
