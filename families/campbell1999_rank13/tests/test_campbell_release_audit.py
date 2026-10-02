from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]

PUBLISHED_BRANCHES = {
    "c1": {
        "sextuple": [0, 87, 164, 264, 375, 452],
        "extra_x": "(7/31)*u+(10848/31)",
    },
    "c2": {
        "sextuple": [0, 55, 146, 255, 260, 346],
        "extra_x": "(-7/27)*u+(6920/27)",
    },
    "c3": {
        "sextuple": [0, 355, 602, 910, 1580, 1827],
        "extra_x": "(19/89)*u+(127890/89)",
    },
    "c4": {
        "sextuple": [0, 97, 104, 129, 500, 532],
        "extra_x": "(1/23)*u+(9804/23)",
    },
    "c5": {
        "sextuple": [0, 42, 47, 82, 152, 175],
        "extra_x": "(1/21)*u+(410/3)",
    },
    "c6": {
        "sextuple": [0, 37, 62, 110, 180, 205],
        "extra_x": "(7/23)*u+(1271/23)",
    },
}


def _load_subgroup():
    spec = importlib.util.spec_from_file_location(
        "campbell_subgroup_test",
        ROOT / "campbell_subgroup.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_parses_on_current_core_and_exposes_six_variants():
    plugin = read_plugin(ROOT)

    assert plugin.id == "campbell1999_rank13"
    assert plugin.name == "Campbell C1-C6"
    assert plugin.version == "3.0.3"
    assert plugin.plugin_type == "family"
    assert plugin.default_variant_id == "c1"
    assert [variant.id for variant in plugin.variants] == [
        "c1",
        "c2",
        "c3",
        "c4",
        "c5",
        "c6",
    ]
    assert {
        "candidate_generation",
        "family_search",
        "target_search",
        "known_subgroup",
        "quartic_search",
        "pgl2_search",
        "free_search",
    } <= plugin.capabilities


def test_published_campbell_table_matches_manifest_provenance():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    variants = {row["id"]: row for row in manifest["variants"]}

    assert set(variants) == set(PUBLISHED_BRANCHES)
    for branch, expected in PUBLISHED_BRANCHES.items():
        provenance = variants[branch]["provenance"]
        assert provenance["sextuple"] == expected["sextuple"]
        assert provenance["extra_x"] == expected["extra_x"]

    provenance = manifest["provenance"]
    assert provenance["author"] == "Garikai Campbell"
    assert provenance["year"] == 1999
    assert "Chapter 3 §3.3.2" in provenance["citation"]
    assert provenance["source_url"].startswith("https://")
    assert "46–47" in provenance["theorem_reference"]


def test_historical_rank_metadata_is_not_operational_generic_rank():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["historical_generic_rank_lower"] == 13
    assert manifest["generic_rank_claim_state"] == "historical_record"
    assert "generic_rank" not in manifest
    assert "verified_generic_rank_lower" not in manifest

    for variant in manifest["variants"]:
        assert "generic_rank" not in variant
        assert "verified_generic_rank_lower" not in variant
        assert "exact Rank Hunter certification" in variant["provenance"]["claim_boundary"]

    for path in sorted((ROOT / "families").glob("c*.json")):
        family = json.loads(path.read_text(encoding="utf-8"))
        assert "generic_rank" not in family
        assert "verified_generic_rank_lower" not in family
        assert family["historical_generic_rank_lower"] == 13
        assert family["generic_rank_claim_state"] == "historical_record"
        assert family["metadata"]["exact_sections"] == 13
        assert len(family["sections"]) == 13


def test_release_docs_target_current_core_without_stale_08_wording():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    adapter = (ROOT / "search_adapter.py").read_text(encoding="utf-8")

    assert "Rank Hunter **0.9.2**" in readme
    assert "Campbell §3.3.2" in readme
    assert "v0.8" not in readme
    assert "v0.8" not in adapter


def test_current_core_symbolically_validates_all_six_variants():
    result = validate_plugin(read_plugin(ROOT), import_science=True)

    assert result["status"] == "ready"
    assert [row["id"] for row in result["variants"]] == [
        "c1",
        "c2",
        "c3",
        "c4",
        "c5",
        "c6",
    ]
    assert all(row["validation_discriminant_nonzero"] for row in result["variants"])
    assert all("symbolic_validation" in row for row in result["variants"])
    assert result["adapter_contract"]["api_version"] == 1


def test_projection_residuals_and_novelty_ordering():
    mod = _load_subgroup()
    gram = [[2.0, 1.0, 0.0], [1.0, 2.0, 0.0], [0.0, 0.0, 4.0]]
    residuals = mod.projection_residuals(gram, 1)
    assert abs(residuals[0]["residual"] - 1.5) < 1e-12
    assert abs(residuals[0]["relative_residual"] - 0.75) < 1e-12
    assert abs(residuals[1]["residual"] - 4.0) < 1e-12
    assert abs(residuals[1]["relative_residual"] - 1.0) < 1e-12

    records = [
        {"point": (Fraction(1), Fraction(1)), **residuals[0]},
        {"point": (Fraction(2), Fraction(2)), **residuals[1]},
    ]
    ranked = mod.rank_novelty(records)
    assert ranked[0]["relative_residual"] == 1.0


def test_spread_points_is_deterministic_and_bounded():
    mod = _load_subgroup()
    points = [(Fraction(i), Fraction(i * i + 1)) for i in range(10)]
    first = mod.spread_points(points, 4)
    second = mod.spread_points(list(reversed(points)), 4)

    assert first == second
    assert len(first) == 4
    assert first[0] == points[0]
    assert first[-1] == points[-1]
