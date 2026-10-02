from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = spec_from_file_location("dujella_peral_adapter_test", ROOT / "search_adapter.py")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_family_and_target_search_options_are_declared():
    mod = _load()
    family = {rec["key"]: rec for rec in mod.search_options(context="family")}
    target = {rec["key"]: rec for rec in mod.search_options(context="target")}
    for defs in (family, target):
        assert {"stages", "timeout", "max_points", "model_prep_timeout", "include_generic", "exact_candidates", "certificate_timeout"} <= set(defs)
        assert all(rec.get("help") for rec in defs.values())
        assert all(rec.get("group") for rec in defs.values())
        assert all("group_expanded" in rec for rec in defs.values())
    assert target["stages"]["default"].endswith("1000000")


def test_adapter_dispatches_to_plugin_local_runner():
    mod = _load()
    family = mod.build_family_search_command(
        python="python",
        db="rank42.db",
        candidate_file="candidate.jsonl",
        options={"stages": "1000,10000", "timeout": 7, "max_points": 11, "model_prep_timeout": 3, "include_generic": True},
    )
    target = mod.build_target_search_command(
        python="python",
        db="rank42.db",
        curve_id=17,
        options={"stages": "1000,10000,100000", "timeout": 9, "max_points": 13, "model_prep_timeout": 4, "include_generic": True},
    )
    assert Path(family[1]).resolve() == (ROOT / "search_runner.py").resolve()
    assert Path(target[1]).resolve() == (ROOT / "search_runner.py").resolve()
    assert family[family.index("--mode") + 1] == "family"
    assert target[target.index("--mode") + 1] == "target"
    assert "--input" in family
    assert "--curve-id" in target
    assert "--include-generic" in family
    assert "--include-generic" in target
    assert not any("rank42.auto_analyze" in piece for piece in family)
    assert not any("rank42.fixed_curve_search" in piece for piece in target)
