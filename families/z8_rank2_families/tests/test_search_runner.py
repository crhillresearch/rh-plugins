import importlib.util,json,sqlite3
from argparse import Namespace
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("z8_runner_test",ROOT/"search_runner.py"); runner=importlib.util.module_from_spec(s); s.loader.exec_module(runner)
def _fixture(tmp_path,variant):
    f=runner._load_variant(variant); u=f.CONTROL_PARAMETER; E=f.curve(u); db=tmp_path/"runner.db"; con=sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE curves (id INTEGER PRIMARY KEY, parameter TEXT, a_invariants_json TEXT)"); con.execute("CREATE TABLE candidates (id INTEGER PRIMARY KEY, curve_id INTEGER)")
        con.execute("INSERT INTO curves(id,parameter,a_invariants_json) VALUES(1,?,?)",(str(u),json.dumps([str(a) for a in E.a_invariants()]))); con.execute("INSERT INTO candidates(id,curve_id) VALUES(7,1)"); con.commit()
    finally: con.close()
    p=tmp_path/"candidate.jsonl"; p.write_text(json.dumps({"_candidate_id":7,"t":str(u),"score":0.0})+"\n",encoding="utf-8"); return db,p
def test_family_runner_is_write_free(tmp_path):
    db,p=_fixture(tmp_path,"dp1"); args=Namespace(db=str(db),mode="family",variant="dp1",input=str(p),curve_id=None,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    before=db.read_bytes(); r=runner.build_result(args); after=db.read_bytes(); assert r["schema"]=="rank42.plugin_geometry_result.v1" and len(r["points"])==2 and before==after
def test_target_runner_preserves_variant(tmp_path):
    db,_=_fixture(tmp_path,"new3"); args=Namespace(db=str(db),mode="target",variant="new3",input=None,curve_id=1,stages=[1000],timeout=1,ratpoints=None,max_points=0,model_prep_timeout=0,include_generic=True)
    r=runner.build_result(args); assert len(r["points"])==2 and r["metadata"]["variant"]=="new3"
