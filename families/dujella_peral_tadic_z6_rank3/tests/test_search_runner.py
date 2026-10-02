import importlib.util
import json
import sqlite3
from argparse import Namespace
from pathlib import Path

import pytest
pytest.importorskip("sage.all")
from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dpt_z6_runner_test", ROOT / "search_runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def _variant(name):
    return runner._load_variant(name)


def _fixture(tmp_path, variant="kihara"):
    family = _variant(variant)
    t = family.CONTROL_PARAMETER
    E = family.curve(t)
    db = tmp_path / "runner.db"
    con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE curves (id INTEGER PRIMARY KEY, parameter TEXT, a_invariants_json TEXT)")
        con.execute("CREATE TABLE candidates (id INTEGER PRIMARY KEY, curve_id INTEGER)")
        con.execute("INSERT INTO curves(id,parameter,a_invariants_json) VALUES(1,?,?)",(str(t),json.dumps([str(a) for a in E.a_invariants()])))
        con.execute("INSERT INTO candidates(id,curve_id) VALUES(7,1)")
        con.commit()
    finally:
        con.close()
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_text(json.dumps({"_candidate_id":7,"t":str(t),"score":0.0})+"\n",encoding="utf-8")
    return db,candidate


def test_family_runner_returns_variant_basis_without_writes(tmp_path):
    db,candidate = _fixture(tmp_path,"kihara")
    args = Namespace(db=str(db),mode="family",variant="kihara",input=str(candidate),curve_id=None,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    before=db.read_bytes()
    result=runner.build_result(args)
    after=db.read_bytes()
    assert result["schema"] == "rank42.plugin_geometry_result.v1"
    assert result["status"] == "completed"
    assert len(result["points"]) == 3
    assert result["metadata"]["variant"] == "kihara"
    assert result["metadata"]["generic_sections_returned"] == 3
    assert before == after


def test_target_runner_uses_requested_variant(tmp_path):
    db,_ = _fixture(tmp_path,"dujella_peral")
    args = Namespace(db=str(db),mode="target",variant="dujella_peral",input=None,curve_id=1,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    result=runner.build_result(args)
    assert len(result["points"]) == 3
    assert result["metadata"]["variant"] == "dujella_peral"
