import json
import sqlite3
import sys
from argparse import Namespace
from pathlib import Path

import pytest

pytest.importorskip("sage.all")
from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import family
import search_runner


def _fixture(tmp_path):
    db = tmp_path / "runner.db"
    E = family.curve(QQ(1))
    con = sqlite3.connect(db)
    try:
        con.execute(
            "CREATE TABLE curves (id INTEGER PRIMARY KEY, parameter TEXT, a_invariants_json TEXT)"
        )
        con.execute(
            "CREATE TABLE candidates (id INTEGER PRIMARY KEY, curve_id INTEGER)"
        )
        con.execute(
            "INSERT INTO curves(id,parameter,a_invariants_json) VALUES(1,?,?)",
            ("1", json.dumps([str(a) for a in E.a_invariants()])),
        )
        con.execute("INSERT INTO candidates(id,curve_id) VALUES(7,1)")
        con.commit()
    finally:
        con.close()
    candidate = tmp_path / "candidate.jsonl"
    candidate.write_text(
        json.dumps({"_candidate_id": 7, "t": "1", "score": 0.0}) + "\n",
        encoding="utf-8",
    )
    return db, candidate


def test_family_runner_returns_published_basis_without_db_writes(tmp_path):
    db, candidate = _fixture(tmp_path)
    args = Namespace(
        db=str(db),
        mode="family",
        input=str(candidate),
        curve_id=None,
        stages=[1000],
        timeout=1,
        ratpoints=None,
        max_points=0,
        model_prep_timeout=0,
        include_generic=True,
    )
    before = db.read_bytes()
    result = search_runner.build_result(args)
    after = db.read_bytes()
    assert result["schema"] == "rank42.plugin_geometry_result.v1"
    assert result["status"] == "completed"
    assert len(result["points"]) == 6
    assert result["metadata"]["generic_sections_returned"] == 6
    assert result["metadata"]["ratpoints_extras_returned"] == 0
    assert before == after


def test_target_runner_can_reconstruct_published_basis(tmp_path):
    db, _candidate = _fixture(tmp_path)
    args = Namespace(
        db=str(db),
        mode="target",
        input=None,
        curve_id=1,
        stages=[1000],
        timeout=1,
        ratpoints=None,
        max_points=0,
        model_prep_timeout=0,
        include_generic=True,
    )
    result = search_runner.build_result(args)
    assert len(result["points"]) == 6
    assert result["metadata"]["mode"] == "target"
