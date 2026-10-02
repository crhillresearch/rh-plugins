import json
from pathlib import Path
from rank42.plugins import read_plugin,validate_plugin
ROOT=Path(__file__).resolve().parents[1]
def test_manifest_contract():
    d=json.loads((ROOT/"plugin.json").read_text(encoding="utf-8")); assert d["id"]=="c2xc4_diophantine_rank4"; assert d["generic_rank"]==4; assert d["verified_generic_rank_lower"]==4; assert d["torsion_groups"]==["C2 × C4"]; assert d["search_adapter"]=="search_adapter.py"; assert d["capabilities"]==["candidate_generation","family_search","target_search","known_subgroup","free_search"]; assert all(p.get("family") and p.get("target") for p in d["search_presets"])
def test_current_core_validates_adapter():
    p=read_plugin(ROOT); r=validate_plugin(p,import_science=False); assert r["status"]=="ready"; assert r["adapter_contract"]["required_methods"]=={"family_search":"build_family_search_command","target_search":"build_target_search_command"}
