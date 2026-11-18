from pathlib import Path

from search_adapter import build_family_search_command, build_target_search_command


def test_commands_use_host_contract_and_sandbox_database():
    family = build_family_search_command(
        python="/sage/python", db="/tmp/sandbox.db",
        candidate_file=Path("/tmp/candidates.jsonl"),
        options={"x_abs_max": 800, "z_max": 1},
    )
    assert family[:2] == ["/sage/python", str(Path(family[1]))]
    assert family[family.index("--db")+1] == "/tmp/sandbox.db"
    assert family[family.index("--input")+1] == "/tmp/candidates.jsonl"
    assert family[family.index("--x-abs-max")+1] == "800"
    target = build_target_search_command(
        python="/sage/python", db="/tmp/sandbox.db", curve_id=42, options={}
    )
    assert target[target.index("--curve-id")+1] == "42"
