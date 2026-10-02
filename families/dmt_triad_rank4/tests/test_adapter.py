import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("dmt_triad_adapter_test",ROOT/"search_adapter.py")
A=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(A)

def test_family_search_delegates_to_core_with_family_spec_and_sections_enabled():
    cmd=A.build_family_search_command(
        python="sage-python",db="rank42.db",candidate_file="pool.jsonl",
        options={"family_spec":"dmt_triad_cef","limit":17},
    )
    assert cmd[:3]==["sage-python","-m","rank42.auto_analyze"]
    assert cmd[cmd.index("--family")+1]=="dmt_triad_cef"
    assert cmd[cmd.index("--limit")+1]=="17"
    assert "--disable-generic-sections" not in cmd
    assert cmd[cmd.index("--quick-strategy")+1]=="pari"

def test_target_search_uses_plugin_worker():
    cmd=A.build_target_search_command(
        python="sage-python",db="rank42.db",curve_id=42,
        options={"family_spec":"dmt_triad_ace"},
    )
    assert cmd[0]=="sage-python"
    assert cmd[1].endswith("target_search.py")
    assert cmd[cmd.index("--curve-id")+1]=="42"
    assert cmd[cmd.index("--family")+1]=="dmt_triad_ace"
