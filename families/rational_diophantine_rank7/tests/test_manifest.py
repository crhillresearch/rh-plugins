import json
from pathlib import Path
from rank42.plugins import read_plugin,validate_plugin

ROOT=Path(__file__).resolve().parents[1]

def test_manifest_contract():
    d=json.loads((ROOT/"plugin.json").read_text(encoding="utf-8"))
    assert d["id"]=="rational_diophantine_rank7"
    assert d["version"]=="0.1.0"
    assert d["generic_rank"]==7
    assert d["verified_generic_rank_lower"]==7
    assert "exact generic rank 7 is not claimed" in d["generic_rank_status"]
    assert d["torsion_groups"]==["C2 × C2"]
    assert d["search_adapter"]=="search_adapter.py"
    assert d["capabilities"]==["candidate_generation","family_search","target_search","known_subgroup","free_search"]
    assert all(p.get("family") and p.get("target") for p in d["search_presets"])

def test_current_core_validates_adapter():
    p=read_plugin(ROOT)
    r=validate_plugin(p,import_science=False)
    assert r["status"]=="ready"
    assert r["adapter_contract"]["required_methods"]=={"family_search":"build_family_search_command","target_search":"build_target_search_command"}
