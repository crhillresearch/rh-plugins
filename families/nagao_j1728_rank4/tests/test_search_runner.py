import importlib.util,json,sqlite3,sys
from argparse import Namespace
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import family
rs=importlib.util.spec_from_file_location("nagao_runner_test",ROOT/"search_runner.py")
runner=importlib.util.module_from_spec(rs); rs.loader.exec_module(runner)

def _fixture(tmp_path):
    t=family.CONTROL_PARAMETER; E=family.curve(t)
    db=tmp_path/"runner.db"; con=sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE curves (id INTEGER PRIMARY KEY, parameter TEXT, a_invariants_json TEXT)")
        con.execute("CREATE TABLE candidates (id INTEGER PRIMARY KEY, curve_id INTEGER)")
        con.execute("INSERT INTO curves(id,parameter,a_invariants_json) VALUES(1,?,?)",(str(t),json.dumps([str(a) for a in E.a_invariants()])))
        con.execute("INSERT INTO candidates(id,curve_id) VALUES(7,1)")
        con.commit()
    finally: con.close()
    p=tmp_path/"candidate.jsonl"; p.write_text(json.dumps({"_candidate_id":7,"t":str(t),"score":0.0})+"\n",encoding="utf-8")
    return db,p

def test_family_runner_returns_four_points_without_writes(tmp_path):
    db,p=_fixture(tmp_path)
    args=Namespace(db=str(db),mode="family",input=str(p),curve_id=None,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    before=db.read_bytes(); r=runner.build_result(args); after=db.read_bytes()
    assert r["schema"]=="rank42.plugin_geometry_result.v1"
    assert len(r["points"])==4
    assert r["metadata"]["j_invariant"]=="1728"
    assert before==after

def test_target_runner_reconstructs_four_points(tmp_path):
    db,_=_fixture(tmp_path)
    args=Namespace(db=str(db),mode="target",input=None,curve_id=1,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    r=runner.build_result(args)
    assert len(r["points"])==4
    assert r["metadata"]["mode"]=="target"
