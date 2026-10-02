from pathlib import Path
from types import SimpleNamespace
import importlib.util
import os

HERE = Path(__file__).resolve().parents[1]


def _load(name):
    path = HERE / name
    spec = importlib.util.spec_from_file_location(f"symmetry_test_{name.replace('.','_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_search_command_hook_wraps_campbell_script():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id":"campbell1999_rank13"},
        "command": ["python", "/x/campbell_chart_search.py", "--mode", "rational", "--charts", "24"],
    }
    out = feature.on_search_command(ctx)
    assert out is not None
    assert out["command"][1].endswith("search_wrapper.py")
    assert out["metadata"]["family_kind"] == "campbell"
    assert out["metadata"]["allow_inversion"] is True


def test_search_command_hook_wraps_mestre_module_but_not_native():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id":"mestre_sextuple_rank11"},
        "command": ["python", "-m", "plugins.mestre_sextuple.chart_search", "--mode", "rational", "--charts", "64"],
    }
    out = feature.on_search_command(ctx)
    assert out is not None
    assert "--original-module" in out["command"]
    assert out["metadata"]["family_kind"] == "mestre"
    assert out["metadata"]["allow_inversion"] is True

    ctx["command"] = ["python", "-m", "plugins.mestre_sextuple.quartic_search", "--mode", "rational"]
    assert feature.on_search_command(ctx) is None


def test_search_command_hook_wraps_kihara_module_as_rational():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id":"kihara2001_rank14"},
        "command": ["python", "-m", "plugins.kihara2001.chart_search", "--charts", "64"],
    }
    out = feature.on_search_command(ctx)
    assert out is not None
    assert out["metadata"]["family_kind"] == "kihara"
    assert out["metadata"]["mode"] == "rational"
    assert out["metadata"]["allow_inversion"] is True


def test_mismatched_family_provenance_refuses_wrap():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id":"kihara2001_rank14"},
        "command": ["python", "-m", "plugins.mestre_sextuple.chart_search", "--mode", "rational"],
    }
    assert feature.on_search_command(ctx) is None


def test_refill_environment_override(monkeypatch):
    feature = _load("feature.py")
    monkeypatch.setenv("RANK42_SYMMETRY_PLAN_MODE", "refill")
    assert feature._plan_mode("mestre") == "refill"
    monkeypatch.setenv("RANK42_SYMMETRY_PLAN_MODE", "nonsense")
    assert feature._plan_mode("mestre") == "dedup"


def test_exact_source_height_dedup_collapses_sign_and_safe_inversion():
    wrapper = _load("search_wrapper.py")

    def chart(a,b,c,d,beta=None,ident="x"):
        return SimpleNamespace(A=a,B=b,C=c,D=d,beta=beta,chart_id=ident)

    charts = [
        chart(3,1,0,-3,None,"a"),
        chart(3,-1,0,3,None,"b"),
        chart(1,3,-3,0,None,"c"),
        chart(1,-3,-3,0,None,"d"),
    ]
    kept, skipped = wrapper._deduplicate(charts, protected_x=set(), allow_inversion=True)
    assert len(kept) == 1
    assert len(skipped) == 3
    assert {x["symmetry"] for x in skipped} <= {"negation","inversion","negative_inversion"}


def test_inversion_not_used_when_boundary_unprotected():
    wrapper = _load("search_wrapper.py")

    def chart(a,b,c,d,beta,ident):
        return SimpleNamespace(A=a,B=b,C=c,D=d,beta=beta,chart_id=ident)

    a = chart(3,1,1,1,3,"a")
    b = chart(1,3,1,1,1,"b")
    kept, skipped = wrapper._deduplicate([a,b], protected_x=set(), allow_inversion=True)
    assert len(kept) == 2
    assert len(skipped) == 0


def test_refill_extends_candidate_pool_until_distinct_budget():
    wrapper = _load("search_wrapper.py")

    def chart(a,b,c,d,ident):
        return SimpleNamespace(A=a,B=b,C=c,D=d,beta=None,chart_id=ident)

    pool = [
        chart(3,1,0,-3,"a"),
        chart(3,-1,0,3,"a-neg"),  # dup of a
        chart(5,1,0,-5,"b"),
        chart(5,-1,0,5,"b-neg"),  # dup of b
        chart(7,2,0,-7,"c"),
        chart(11,3,0,-11,"d"),
        chart(13,4,0,-13,"e"),
        chart(17,5,0,-17,"f"),
    ]

    def planner(coefficients, base_x, discovered_x=None, **kwargs):
        return pool[: int(kwargs.get("limit", 4))]

    audit = {
        "refill_plans":0,
        "planner_candidates_generated":0,
        "refill_extra_candidates":0,
        "refill_shortfall":0,
    }
    kept = wrapper._refill(
        planner,
        ([], set(), []),
        {"limit":4},
        requested=4,
        protected_x=set(),
        allow_inversion=False,
        audit=audit,
        planner_name="test",
    )
    assert len(kept) == 4
    assert [x.chart_id for x in kept] == ["a", "b", "c", "d"]
    assert audit["refill_plans"] == 1


def test_search_command_hook_wraps_v087_kihara_module_alias():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id": "kihara2001_rank14"},
        "command": ["python", "-m", "rank42.kihara_chart_search", "--charts", "64"],
    }
    out = feature.on_search_command(ctx)
    assert out is not None
    assert out["metadata"]["family_kind"] == "kihara"
    assert "--original-module" in out["command"]
    assert "rank42.kihara_chart_search" in out["command"]


def test_search_command_hook_wraps_v087_mestre_module_alias_for_fermigier():
    feature = _load("feature.py")
    ctx = {
        "family_plugin": {"id": "fermigier_rank12_exact"},
        "command": ["python", "-m", "rank42.mestre_chart_search", "--mode", "rational", "--charts", "64"],
    }
    out = feature.on_search_command(ctx)
    assert out is not None
    assert out["metadata"]["family_kind"] == "mestre"
    assert out["metadata"]["family_plugin_id"] == "fermigier_rank12_exact"
