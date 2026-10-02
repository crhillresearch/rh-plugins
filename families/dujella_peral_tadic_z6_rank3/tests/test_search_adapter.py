from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = spec_from_file_location("dpt_z6_adapter_test", ROOT / "search_adapter.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_grouped_family_and_target_options():
    mod = _load()
    for context in ("family","target"):
        defs = mod.search_options(context=context)
        keys = {rec["key"] for rec in defs}
        assert {"stages","timeout","max_points","model_prep_timeout","include_generic","exact_candidates","certificate_timeout"} <= keys
        assert all(rec.get("help") for rec in defs)
        assert all(rec.get("group") for rec in defs)
        assert all("group_expanded" in rec for rec in defs)


def test_commands_preserve_variant():
    mod = _load()
    options = {"plugin_variant":"eroshkin_minus","stages":"1000,10000","timeout":7,"max_points":11,"model_prep_timeout":3,"include_generic":True}
    fam = mod.build_family_search_command(python="python",db="rank42.db",candidate_file="candidate.jsonl",options=options)
    tar = mod.build_target_search_command(python="python",db="rank42.db",curve_id=17,options=options)
    for cmd in (fam,tar):
        assert cmd[cmd.index("--variant")+1] == "eroshkin_minus"
        assert Path(cmd[1]).resolve() == (ROOT / "search_runner.py").resolve()
        assert "--include-generic" in cmd
    assert "--input" in fam
    assert "--curve-id" in tar
