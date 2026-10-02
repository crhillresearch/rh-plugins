import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_adapter():
    spec = importlib.util.spec_from_file_location("fermigier_search_adapter_test", ROOT / "search_adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_declares_plugin_local_family_file():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.1.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["verified_generic_rank_lower"] == 12
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert manifest["family"]["kind"] == "module"
    assert manifest["family"]["file"] == "family.py"
    # Keep the released logical spec stable for stored Rank Hunter provenance.
    assert manifest["family"]["spec"] == "plugins.fermigier_rank12_exact.family"


def test_search_adapter_launches_plugin_local_files():
    adapter = _load_adapter()
    native = adapter.build_family_search_command(
        python="/sage/python", db="/tmp/rank42.db", candidate_file="/tmp/candidates.jsonl",
        options={"adapter": "native"},
    )
    pgl2 = adapter.build_target_search_command(
        python="/sage/python", db="/tmp/rank42.db", curve_id=13,
        options={"adapter": "pgl2"},
    )
    assert native[1] == str(ROOT / "native_search.py")
    assert pgl2[1] == str(ROOT / "chart_search.py")
    assert "-m" not in native[:3]
    assert "-m" not in pgl2[:3]


def test_runtime_scripts_do_not_import_old_plugins_package_path():
    for name in ("native_search.py", "chart_search.py", "doctor.py", "search_adapter.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "from plugins.fermigier_rank12_exact" not in text
        assert "-m','plugins.fermigier_rank12_exact" not in text


def test_search_runner_uses_current_general_hunt_core_and_plugin_local_subgroup_helpers():
    text = (ROOT / "native_search.py").read_text(encoding="utf-8")
    assert "from rank42.general_hunt_core import canonical_affine_key, parse_height_stages" in text
    assert "high_rank_playground_core" not in text
    assert "subgroup_focus_core" not in text
    assert (ROOT / "subgroup_focus.py").is_file()
