from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load_adapter():
    spec = spec_from_file_location("mestre_adapter_test", ROOT / "search_adapter.py")
    mod = module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_native_and_chart_dispatch_are_plugin_local():
    mod = load_adapter()
    native = mod.build_family_search_command(
        python="python", db="rank42.db", candidate_file="candidates.jsonl",
        options={"adapter": "native", "stages": "1000"},
    )
    chart = mod.build_target_search_command(
        python="python", db="rank42.db", curve_id=9,
        options={"adapter": "pgl2", "stages": "1000", "charts": 12},
    )
    assert Path(native[1]).resolve() == (ROOT / "native_search.py").resolve()
    assert Path(chart[1]).resolve() == (ROOT / "seeded_chart_search.py").resolve()
    assert not any("rank42.mestre" in piece for piece in native + chart)


def test_context_defaults_differ_for_target():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.5.2"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["verified_generic_rank_lower"] == 11
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    family = {x["key"]: x["default"] for x in manifest["search_options"]["family"]}
    target = {x["key"]: x["default"] for x in manifest["search_options"]["target"]}
    assert family["adapter"] == "native"
    assert target["adapter"] == "pgl2"
