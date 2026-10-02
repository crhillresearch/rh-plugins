import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ["lecacheux","kihara","eroshkin_plus","eroshkin_minus","dujella_peral","macleod"]


def test_manifest_has_six_searchable_variants():
    data = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert data["id"] == "dujella_peral_tadic_z6_rank3"
    assert data["version"] == "0.1.0"
    assert data["default_variant"] == "kihara"
    assert [rec["id"] for rec in data["variants"]] == EXPECTED
    assert data["capabilities"] == ["candidate_generation","family_search","target_search","known_subgroup","free_search"]
    assert data["search_adapter"] == "search_adapter.py"
    assert all(rec["torsion_groups"] == ["C6"] for rec in data["variants"])
    assert all(rec["verified_generic_rank_lower"] == 3 for rec in data["variants"])
    assert all(rec.get("family") and rec.get("target") for rec in data["search_presets"])


def test_current_core_validates_adapter_contract():
    plugin = read_plugin(ROOT)
    assert len(plugin.variants) == 6
    report = validate_plugin(plugin, import_science=False)
    assert report["status"] == "ready"
    assert report["adapter_contract"]["required_methods"] == {
        "family_search": "build_family_search_command",
        "target_search": "build_target_search_command",
    }
