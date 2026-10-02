import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin

ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_contract():
    data = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert data["id"] == "dujella_peral_z4_rank6"
    assert data["version"] == "0.1.1"
    assert data["minimum_rank_hunter_version"] == "0.9.2"
    assert data["historical_generic_rank_lower"] == 6
    assert data["verified_generic_rank_lower"] == 6
    assert data["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert data["torsion_groups"] == ["C4"]
    assert data["torsion_provider_role"] == "prescribed_subfamily"
    assert data["search_adapter"] == "search_adapter.py"
    assert data["capabilities"] == [
        "candidate_generation",
        "family_search",
        "target_search",
        "known_subgroup",
        "free_search",
    ]
    assert {"family", "target"} == set(data["search_options"])
    assert all(rec.get("family") and rec.get("target") for rec in data["search_presets"])


def test_current_core_parses_and_validates_adapter_contract():
    plugin = read_plugin(ROOT)
    assert plugin.id == "dujella_peral_z4_rank6"
    assert plugin.plugin_type == "family"
    assert plugin.generic_rank == 6
    assert plugin.verified_generic_rank_lower == 6
    report = validate_plugin(plugin, import_science=False)
    assert report["status"] == "ready"
    assert report["adapter_contract"]["required_methods"] == {
        "family_search": "build_family_search_command",
        "target_search": "build_target_search_command",
    }
