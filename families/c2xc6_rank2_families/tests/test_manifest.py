import json
from pathlib import Path
from rank42.plugins import read_plugin, validate_plugin

ROOT=Path(__file__).resolve().parents[1]
EXPECTED=["dp1","dp2","dp3","hadano","new1"]

def test_manifest_has_five_searchable_variants():
    d=json.loads((ROOT/"plugin.json").read_text(encoding="utf-8"))
    assert d["id"]=="c2xc6_rank2_families"
    assert d["version"]=="0.1.0"
    assert [v["id"] for v in d["variants"]]==EXPECTED
    assert d["capabilities"]==["candidate_generation","family_search","target_search","known_subgroup","free_search"]
    assert d["search_adapter"]=="search_adapter.py"
    assert all(v["torsion_groups"]==["C2 × C6"] for v in d["variants"])
    assert all(v["verified_generic_rank_lower"]==2 for v in d["variants"])
    assert all(p.get("family") and p.get("target") for p in d["search_presets"])

def test_current_core_validates_adapter_contract():
    p=read_plugin(ROOT)
    assert len(p.variants)==5
    r=validate_plugin(p,import_science=False)
    assert r["status"]=="ready"
    assert r["adapter_contract"]["required_methods"]=={"family_search":"build_family_search_command","target_search":"build_target_search_command"}
