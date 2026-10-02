import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fibonacci_triples_adapter_test", ROOT / "adapter.py")
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def test_adapter_keeps_generic_sections_enabled():
    cmd = adapter.build_family_search_command(
        python="/science/python",
        db="rank42.db",
        candidate_file="pool.jsonl",
        options={
            "family_spec": "fibonacci_triples_odd",
            "limit": 7,
            "quick_timeout": 11,
            "strong_timeout": 22,
            "generic_certificate_timeout": 33,
            "quick_only": True,
            "fast_screen": True,
        },
    )
    assert cmd[:3] == ["/science/python", "-m", "rank42.auto_analyze"]
    assert "--family" in cmd and "fibonacci_triples_odd" in cmd
    assert "--quick-only" in cmd
    assert cmd[cmd.index("--quick-strategy") + 1] == "pari"
    assert "--fast-screen" in cmd
    assert "--no-generic-witness" not in cmd


def test_target_adapter_dispatches_family_aware_worker():
    cmd = adapter.build_target_search_command(
        python="/science/python",
        db="rank42.db",
        curve_id=42,
        options={
            "family_spec": "fibonacci_triples_even",
            "quick_timeout": 9,
            "strong_timeout": 18,
            "generic_certificate_timeout": 27,
            "quick_only": True,
            "fast_screen": True,
        },
    )
    assert cmd[0] == "/science/python"
    assert Path(cmd[1]).name == "target_search.py"
    assert cmd[cmd.index("--curve-id") + 1] == "42"
    assert cmd[cmd.index("--family") + 1] == "fibonacci_triples_even"
    assert "--quick-only" in cmd
    assert cmd[cmd.index("--quick-strategy") + 1] == "pari"
    assert "--fast-screen" in cmd
    assert "--no-generic-witness" not in cmd


def _manifest_search_options(context):
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    return list((manifest.get("search_options") or {}).get(context) or [])


def test_target_context_exposes_controls():
    keys = {rec["key"] for rec in _manifest_search_options("target")}
    assert {"quick_timeout", "strong_timeout", "quick_only", "fast_screen", "generic_certificate_timeout"} <= keys


def test_pari_screen_is_the_plugin_default():
    defs = {rec["key"]: rec for rec in _manifest_search_options("family")}
    assert defs["quick_only"]["default"] is True
    assert "PARI" in defs["quick_only"]["label"]


def test_command_builder_defaults_to_quick_only_when_option_is_absent():
    cmd = adapter.build_family_search_command(
        python="/science/python",
        db="rank42.db",
        candidate_file="pool.jsonl",
        options={"family_spec": "fibonacci_triples_odd", "limit": 1},
    )
    assert "--quick-only" in cmd
    assert cmd[cmd.index("--quick-strategy") + 1] == "pari"
