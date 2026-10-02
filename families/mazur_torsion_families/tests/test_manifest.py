import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "plugin.json").read_text())

EXPECTED = {
    "Trivial": 31,
    "C2": 20,
    "C3": 15,
    "C4": 13,
    "C5": 9,
    "C6": 9,
    "C7": 6,
    "C8": 6,
    "C9": 4,
    "C10": 4,
    "C12": 4,
    "C2 × C2": 15,
    "C2 × C4": 9,
    "C2 × C6": 6,
    "C2 × C8": 3,
}





def test_release_version_and_sources_are_current():
    assert MANIFEST["version"] == "0.1.5"
    assert MANIFEST["minimum_rank_hunter_version"] == "0.9.2"
    assert MANIFEST["capabilities"] == ["candidate_generation"]
    assert MANIFEST["default_variant"] == "c2xc8"

    provenance = MANIFEST["provenance"]
    assert provenance["classification"]["doi"] == "10.1007/BF02684339"
    assert provenance["record_table"]["as_of"] == "2026-10-02"
    assert provenance["record_table"]["status"].startswith("Checked during")

    for variant in MANIFEST["variants"]:
        assert variant["torsion_record"]["source"]["as_of"] == "2026-10-02"


def test_manifest_has_all_15_mazur_groups_once():
    variants = MANIFEST["variants"]
    assert len(variants) == 15
    groups = [v["torsion_groups"][0] for v in variants]
    assert set(groups) == set(EXPECTED)
    assert len(groups) == len(set(groups))


def test_record_goals_are_record_plus_one():
    for variant in MANIFEST["variants"]:
        group = variant["torsion_groups"][0]
        record = variant["torsion_record"]
        assert record["rank_lower"] == EXPECTED[group]
        assert record["goal_rank"] == EXPECTED[group] + 1


def test_every_variant_has_a_family_file_and_direct_provider_role():
    for variant in MANIFEST["variants"]:
        assert variant["torsion_provider_role"] in {
            "canonical_universal",
            "prescribed_subfamily",
        }
        path = ROOT / variant["family"]["file"]
        assert path.exists()
        data = json.loads(path.read_text())
        assert len(data["a_invariants"]) == 5
        assert data["generic_rank"] is None


def test_formula_family_candidate_defaults_are_laptop_safe():
    preset_groups = [MANIFEST.get("search_presets", [])]
    for variant in MANIFEST["variants"]:
        defaults = variant["candidate_defaults"]
        bounds = [int(value) for value in defaults["stage_bounds"].split(",")]
        assert bounds == sorted(set(bounds))
        assert bounds[-1] <= 2000

        preset_groups.append(variant.get("search_presets", []))

    for presets in preset_groups:
        for preset in presets:
            candidate = preset.get("candidate") or {}
            if not candidate:
                continue
            preset_bounds = [
                int(value) for value in candidate["stage_bounds"].split(",")
            ]
            assert preset_bounds == sorted(set(preset_bounds))
            assert preset_bounds[-1] <= 2000


def test_low_level_twist_sensitive_classes_are_not_called_universal():
    by_group = {
        v["torsion_groups"][0]: v
        for v in MANIFEST["variants"]
    }
    for group in ("Trivial", "C2", "C3", "C2 × C2"):
        assert by_group[group]["torsion_provider_role"] == "prescribed_subfamily"


def test_c2xc8_is_record_3_goal_4_canonical_direct_lane():
    variant = next(v for v in MANIFEST["variants"] if v["id"] == "c2xc8")
    assert variant["torsion_groups"] == ["C2 × C8"]
    assert variant["torsion_provider_role"] == "canonical_universal"
    assert variant["torsion_record"]["rank_lower"] == 3
    assert variant["torsion_record"]["goal_rank"] == 4
    assert variant["auto_search"]["target_rank"] == 4


def test_c2xc8_target_presets_include_deep_and_geometry_expansion():
    variant = next(v for v in MANIFEST["variants"] if v["id"] == "c2xc8")
    presets = {rec["id"]: rec for rec in variant["search_presets"]}

    assert presets["deep"]["target"] == {
        "backend": "Torsion",
        "pipeline_preset": "aggressive_rank_hunter",
        "goal_rank": 4,
        "ratpoints_backend": "GPU",
    }
    assert presets["fiber_expansion"]["target"]["backend"] == "Torsion"
    assert presets["fiber_expansion"]["target"]["pipeline_preset"] == "geometry"
    assert presets["fiber_expansion"]["target"]["goal_rank"] == 4
    assert presets["generator_breaker"]["target"]["pipeline_preset"] == "generator_breaker"
    assert presets["geometry_grinder"]["target"]["pipeline_preset"] == "geometry_grinder"


def test_c2xc8_target_presets_never_claim_rank_evidence():
    variant = next(v for v in MANIFEST["variants"] if v["id"] == "c2xc8")
    for rec in variant["search_presets"]:
        target = rec.get("target") or {}
        if not target:
            continue
        assert target["backend"] == "Torsion"
        assert target["goal_rank"] == 4
        assert set(target) <= {
            "backend",
            "pipeline_preset",
            "goal_rank",
            "ratpoints_backend",
        }


def test_c2xc8_target_presets_include_arithmetic_escalation_buttons():
    variant = next(v for v in MANIFEST["variants"] if v["id"] == "c2xc8")
    presets = {rec["id"]: rec for rec in variant["search_presets"]}

    expected = {
        "selmer_gate": "selmer_gate",
        "covering_forest": "covering_forest",
        "isogeny_hunt": "isogeny_hunt",
        "arithmetic_siege": "arithmetic_siege",
    }
    for preset_id, pipeline_preset in expected.items():
        target = presets[preset_id]["target"]
        assert target["backend"] == "Torsion"
        assert target["pipeline_preset"] == pipeline_preset
        assert target["goal_rank"] == 4
        assert target["ratpoints_backend"] == "GPU"


def test_current_core_exact_torsion_validation_for_all_variants():
    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)
    assert result["status"] == "ready"
    assert result["plugin_version"] == "0.1.5"
    assert result["default_variant"] == "c2xc8"
    assert len(result["variants"]) == 15

    expected = {
        variant["id"]: variant["torsion_groups"][0]
        for variant in MANIFEST["variants"]
    }
    by_id = {row["id"]: row for row in result["variants"]}
    assert set(by_id) == set(expected)
    for variant_id, torsion in expected.items():
        row = by_id[variant_id]
        assert row["validation_parameter"] == "2"
        assert row["validation_discriminant_nonzero"] is True
        assert row["validation_torsion"] == torsion
        assert row["family_generic_rank"] is None


def test_no_generic_rank_evidence_is_declared_anywhere():
    assert "generic_rank" not in MANIFEST
    assert "historical_generic_rank_lower" not in MANIFEST
    assert "verified_generic_rank_lower" not in MANIFEST
    for variant in MANIFEST["variants"]:
        assert "generic_rank" not in variant
        assert "historical_generic_rank_lower" not in variant
        assert "verified_generic_rank_lower" not in variant
        data = json.loads((ROOT / variant["family"]["file"]).read_text())
        assert data["generic_rank"] is None
        assert data["sections"] == []


def test_release_readme_is_portable():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Rank Hunter **0.9.2**" in readme
    assert "exact rational torsion subgroup" in readme
    assert "2026-10-02" in readme
    assert "/home/" not in readme
    assert "/Users/" not in readme
    assert "miniforge3" not in readme
