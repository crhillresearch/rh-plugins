from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def _load():
    s=spec_from_file_location("z8_adapter_test",ROOT/"search_adapter.py"); m=module_from_spec(s); s.loader.exec_module(m); return m
def test_options_and_variant_dispatch():
    m=_load()
    for context in ("family","target"):
        defs=m.search_options(context=context); keys={r["key"] for r in defs}
        assert {"stages","timeout","max_points","model_prep_timeout","include_generic","exact_candidates","certificate_timeout"}<=keys
        assert all(r.get("help") and r.get("group") and "group_expanded" in r for r in defs)
    opts={"plugin_variant":"new3","stages":"1000,10000","timeout":7,"max_points":11,"model_prep_timeout":3,"include_generic":True}
    fam=m.build_family_search_command(python="python",db="rank42.db",candidate_file="candidate.jsonl",options=opts)
    tar=m.build_target_search_command(python="python",db="rank42.db",curve_id=17,options=opts)
    assert fam[fam.index("--variant")+1]=="new3" and tar[tar.index("--variant")+1]=="new3"
    assert "--input" in fam and "--curve-id" in tar
