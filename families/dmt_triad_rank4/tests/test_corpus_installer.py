import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dmt_curves2_installer", ROOT / "build_curves2.py"
)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def _write_corpus(path, *, curves=2, observations=3):
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE corpus_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE curves(id INTEGER PRIMARY KEY, exact_rank INTEGER);
        CREATE TABLE observations(id INTEGER PRIMARY KEY);
        """
    )
    db.execute("INSERT INTO corpus_meta VALUES('schema_version','1')")
    db.execute("INSERT INTO corpus_meta VALUES('built_at','2026-09-21T20:10:51Z')")
    db.execute("INSERT INTO corpus_meta VALUES('failed_artifacts','0')")
    for i in range(curves):
        db.execute(
            "INSERT INTO curves(id,exact_rank) VALUES(?,?)",
            (i + 1, 10 if i == 0 else None),
        )
    for i in range(observations):
        db.execute("INSERT INTO observations(id) VALUES(?)", (i + 1,))
    db.commit()
    db.close()


def test_validate_corpus_accepts_populated_schema(tmp_path):
    path = tmp_path / "curves2.db"
    _write_corpus(path)
    stats = installer._validate_corpus(path)
    assert stats["curves"] == 2
    assert stats["observations"] == 3
    assert stats["exact_curves"] == 1
    assert stats["failed_artifacts"] == 0


def test_validate_corpus_rejects_empty_evidence(tmp_path):
    path = tmp_path / "curves2.db"
    _write_corpus(path, curves=0, observations=0)
    try:
        installer._validate_corpus(path)
    except RuntimeError as exc:
        assert "no usable curve evidence" in str(exc)
    else:
        raise AssertionError("empty corpus should be rejected")


def test_latest_successful_run_filters_to_source_branch(monkeypatch):
    monkeypatch.setattr(
        installer,
        "_gh_json",
        lambda args: {
            "workflow_runs": [
                {"id": 1, "conclusion": "success", "head_branch": "wrong"},
                {
                    "id": 2,
                    "conclusion": "success",
                    "head_branch": installer.SOURCE_REF,
                },
            ]
        },
    )
    assert installer._latest_successful_run_id() == 2
