from pathlib import Path
import importlib.util
import json
import sqlite3
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "twist_isogeny_lab_backend_test",
    ROOT / "backend.py",
)
B = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = B
spec.loader.exec_module(B)


def _db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE curves(
            id INTEGER PRIMARY KEY,
            family TEXT,
            parameter TEXT,
            a_invariants_json TEXT,
            score REAL,
            root_number INTEGER,
            generic_lower INTEGER,
            descent_lower INTEGER,
            exact_rank INTEGER,
            conductor TEXT,
            discriminant TEXT
        )
        """
    )
    db.executemany(
        """
        INSERT INTO curves(
            id,family,parameter,a_invariants_json,score,root_number,
            generic_lower,descent_lower,exact_rank,conductor,discriminant
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            (
                1, "Demo", "1/2", '["0","0","1","-1","0"]',
                12.5, -1, 2, 3, None, "37", "-37"
            ),
            (
                2, "Demo", "2/3", '["0","0","1","-1","0"]',
                None, 1, 2, 2, 2, "37", "-37"
            ),
            (
                3, "Other", "1", '["0","0","0","-1","0"]',
                3.0, None, None, None, None, None, None
            ),
        ],
    )
    db.commit()
    return db


def test_list_stored_curves_is_read_only_and_projects_rank_fields():
    db = _db()
    before = db.total_changes
    rows = B.list_stored_curves(db)
    after = db.total_changes

    assert after == before
    assert [row.curve_id for row in rows] == [3, 2, 1]
    assert next(row for row in rows if row.curve_id == 1).rigorous_lower == 3
    assert next(row for row in rows if row.curve_id == 2).rigorous_lower == 2


def test_parse_ainvs_accepts_list_and_named_shape_only():
    assert B.parse_ainvs('["0","0","1","-1","0"]') == ("0", "0", "1", "-1", "0")
    assert B.parse_ainvs(
        {"a1": 0, "a2": 0, "a3": 1, "a4": -1, "a6": 0}
    ) == ("0", "0", "1", "-1", "0")
    assert B.parse_ainvs("[1,2,3]") is None
    assert B.parse_ainvs("not-json") is None


def test_stored_model_index_keeps_duplicate_exact_models_visible():
    rows = B.list_stored_curves(_db())
    index = B.stored_model_index(rows)
    matches = index[B.model_key(("0", "0", "1", "-1", "0"))]
    assert {row.curve_id for row in matches} == {1, 2}




def test_model_key_canonicalizes_equivalent_rational_coefficients():
    assert B.model_key(("0", "0/1", "1", "-1", "0")) == B.model_key(
        (0, 0, 1, "-2/2", 0)
    )


def test_model_key_rejects_non_rational_coefficients():
    try:
        B.model_key(("0", "0", "sqrt(2)", "-1", "0"))
    except ValueError as exc:
        assert "invalid rational coefficient" in str(exc)
    else:
        raise AssertionError("non-rational coefficient should not be accepted")

def test_worker_cache_key_depends_on_curve_and_exact_model():
    row = next(row for row in B.list_stored_curves(_db()) if row.curve_id == 1)
    key = B.worker_cache_key(row)
    assert key.startswith("1:")
    assert B.model_key(row.ainvs) in key


def test_run_worker_is_bounded_json_subprocess_without_shell(monkeypatch, tmp_path):
    worker = tmp_path / "worker.py"
    worker.write_text("# placeholder", encoding="utf-8")
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "schema": B.WORKER_SCHEMA,
                    "source_index": 0,
                    "nodes": [{"index": 0, "ainvs": ["0","0","1","-1","0"]}],
                    "edges": [],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    payload = B.run_isogeny_worker(
        science_python="/science/python",
        worker_path=worker,
        ainvs=("0", "0", "1", "-1", "0"),
        timeout=23,
    )

    assert payload["schema"] == B.WORKER_SCHEMA
    assert seen["args"] == ["/science/python", str(worker.resolve())]
    assert seen["kwargs"]["timeout"] == 23
    assert seen["kwargs"]["capture_output"] is True
    assert "shell" not in seen["kwargs"]


def test_backend_contains_no_database_write_sql():
    text = (ROOT / "backend.py").read_text(encoding="utf-8").upper()
    for verb in ("INSERT INTO", "UPDATE CURVES", "DELETE FROM", "REPLACE INTO"):
        assert verb not in text



def test_twist_cache_key_depends_on_bound():
    row = next(row for row in B.list_stored_curves(_db()) if row.curve_id == 1)
    assert B.twist_cache_key(row, 50).endswith(":twists:50")
    assert B.twist_cache_key(row, 250).endswith(":twists:250")


def test_run_twist_worker_clamps_bound_and_validates_schema(monkeypatch, tmp_path):
    worker = tmp_path / "twist_worker.py"
    worker.write_text("# placeholder", encoding="utf-8")
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        seen["request"] = json.loads(kwargs["input"])
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "schema": B.TWIST_SCHEMA,
                    "bound": 250,
                    "source_ainvs": ["0","0","1","-1","0"],
                    "twists": [
                        {
                            "d": 1,
                            "ainvs": ["0","0","1","-1","0"],
                            "minimal_ainvs": ["0","0","1","-1","0"],
                            "conductor": "37",
                            "discriminant": "-37",
                            "j_invariant": "0",
                            "root_number": -1,
                            "torsion_invariants": [],
                            "bad_primes": [37],
                        }
                    ],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    payload = B.run_twist_worker(
        science_python="/science/python",
        worker_path=worker,
        ainvs=("0", "0", "1", "-1", "0"),
        bound=999,
        timeout=41,
    )

    assert payload["schema"] == B.TWIST_SCHEMA
    assert seen["args"] == ["/science/python", str(worker.resolve())]
    assert seen["request"]["bound"] == 250
    assert seen["kwargs"]["timeout"] == 41
    assert "shell" not in seen["kwargs"]



def test_full_isogeny_timeout_uses_distinct_inconclusive_exception(monkeypatch, tmp_path):
    worker = tmp_path / "worker.py"
    worker.write_text("# placeholder", encoding="utf-8")

    def fake_run(*args, **kwargs):
        raise B.subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    try:
        B.run_isogeny_worker(
            science_python="/science/python",
            worker_path=worker,
            ainvs=("0", "0", "1", "-1", "0"),
            timeout=7,
        )
    except B.WorkerTimeout as exc:
        assert "timed out after 7s" in str(exc)
    else:
        raise AssertionError("timeout must remain explicitly inconclusive")


def test_probe_cache_key_tracks_degrees_and_timeout():
    row = next(row for row in B.list_stored_curves(_db()) if row.curve_id == 1)
    key = B.probe_cache_key(row, (2, 3, 5), 12)
    assert key.endswith(":probe:2,3,5:12")


def test_isogeny_probe_keeps_exact_completed_degrees_and_timeouts_separate(
    monkeypatch, tmp_path
):
    worker = tmp_path / "probe.py"
    worker.write_text("# placeholder", encoding="utf-8")
    calls = []

    def fake_run(args, **kwargs):
        request = json.loads(kwargs["input"])
        degree = request["degree"]
        calls.append(degree)
        if degree == 3:
            raise B.subprocess.TimeoutExpired(cmd=args, timeout=kwargs["timeout"])
        hits = []
        if degree == 2:
            hits.append(
                {
                    "degree": 2,
                    "domain_ainvs": ["0","0","1","-1","0"],
                    "codomain_ainvs": ["0","0","1","-4","0"],
                    "codomain_conductor": "37",
                    "codomain_discriminant": "-2368",
                    "codomain_j_invariant": "0",
                }
            )
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "schema": B.PROBE_SCHEMA,
                    "degree": degree,
                    "isogenies": hits,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(B.subprocess, "run", fake_run)
    result = B.run_isogeny_probe(
        science_python="/science/python",
        worker_path=worker,
        ainvs=("0", "0", "1", "-1", "0"),
        primes=(2, 3, 5),
        per_degree_timeout=9,
    )

    assert calls == [2, 3, 5]
    assert result["checked_degrees"] == [2, 5]
    assert result["timed_out_degrees"] == [3]
    assert [item["degree"] for item in result["hits"]] == [2]
    assert result["complete_for_requested_degrees"] is False
