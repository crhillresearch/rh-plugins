from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def _load():
    s=spec_from_file_location("nagao_adapter_test",ROOT/"search_adapter.py"); m=module_from_spec(s); s.loader.exec_module(m); return m
def test_options_and_dispatch():
    m=_load()
    for context in ("family","target"):
        defs=m.search_options(context=context); keys={r["key"] for r in defs}
        assert {"stages","timeout","max_points","model_prep_timeout","include_generic","exact_candidates","certificate_timeout"}<=keys
        assert all(r.get("help") and r.get("group") and "group_expanded" in r for r in defs)
    opts={"stages":"1000,10000","timeout":7,"max_points":11,"model_prep_timeout":3,"include_generic":True}
    fam=m.build_family_search_command(python="python",db="rank42.db",candidate_file="candidate.jsonl",options=opts)
    tar=m.build_target_search_command(python="python",db="rank42.db",curve_id=17,options=opts)
    assert Path(fam[1]).resolve()==(ROOT/"search_runner.py").resolve()
    assert Path(tar[1]).resolve()==(ROOT/"search_runner.py").resolve()
    assert "--input" in fam and "--curve-id" in tar
