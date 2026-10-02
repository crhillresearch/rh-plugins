from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sqlite3


HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("leaderboard_compare_backend_test", HERE / "backend.py")
B = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = B
spec.loader.exec_module(B)


def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE curves (
            id INTEGER PRIMARY KEY,
            family TEXT,
            parameter TEXT,
            conductor TEXT,
            discriminant TEXT,
            exact_rank INTEGER,
            descent_lower INTEGER,
            generic_lower INTEGER,
            torsion_label TEXT,
            updated_at TEXT
        );
        CREATE TABLE external_catalogs (
            source TEXT PRIMARY KEY,
            source_url TEXT,
            curve_count INTEGER,
            best_rank_lower INTEGER,
            snapshot_path TEXT,
            raw_sha256 TEXT,
            fetched_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE external_curves (
            source TEXT,
            source_id TEXT,
            rank_lower_bound INTEGER,
            conductor TEXT,
            discriminant TEXT,
            naive_height TEXT,
            faltings_height TEXT,
            source_url TEXT,
            submitter TEXT,
            source_updated_at TEXT,
            raw_json TEXT,
            active INTEGER
        );
        """
    )
    return conn


def test_log_big_int_matches_normal_log_and_huge_power():
    assert B.log_big_int("1000") == math.log(1000)
    assert B.log_big_int("-1000") == math.log(1000)
    assert abs(B.log_big_int("1" + "0" * 100) - 100 * math.log(10)) < 1e-12
    assert B.log_big_int("0") is None
    assert B.log_big_int("not-an-int") is None


def test_local_loader_uses_strongest_stored_rigorous_lower():
    conn = db()
    conn.executemany(
        """
        INSERT INTO curves(
            id,family,parameter,conductor,discriminant,
            exact_rank,descent_lower,generic_lower,torsion_label,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        [
            (1, "A", "1", "100", "-200", None, 17, 2, "C2", "now"),
            (2, "B", "2", "50", "-300", 18, 18, 2, "C2 × C4", "now"),
            (3, "A", "3", "10", "-400", None, 16, 2, None, "now"),
        ],
    )
    rows = B.load_local_points(conn, min_rank=17, max_rank=30)
    assert [(p.source_id, p.rank_lower, p.rank_evidence) for p in rows] == [
        ("1", 17, "rank ≥ 17"),
        ("2", 18, "rank = 18"),
    ]


def test_icarm_loader_ignores_inactive_rows():
    conn = db()
    conn.executemany(
        """
        INSERT INTO external_curves(
            source,source_id,rank_lower_bound,conductor,discriminant,
            naive_height,faltings_height,source_url,submitter,source_updated_at,raw_json,active
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            ("icarm", "10", 17, "1000", "-5000", "12.5", "2.5", "https://x/10", "A", "now", '{"torsion":[2,4]}', 1),
            ("icarm", "11", 20, "900", "-6000", "13.5", "3.5", "https://x/11", "B", "now", '{"torsion":[3]}', 0),
        ],
    )
    rows = B.load_icarm_points(conn, min_rank=17, max_rank=30)
    assert [p.source_id for p in rows] == ["10"]
    assert rows[0].naive_height == 12.5
    assert rows[0].torsion_label == "C2 × C4"


def point(source, source_id, rank, conductor):
    return B.ChartPoint(
        source=source,
        source_label="Rank Hunter" if source == B.LOCAL_SOURCE else "ICARM",
        source_id=str(source_id),
        rank_lower=rank,
        rank_evidence=f"rank ≥ {rank}",
        family="f",
        parameter="",
        conductor=str(conductor),
        discriminant=None,
        naive_height=None,
        faltings_height=None,
    )


def test_best_per_rank_is_separate_for_each_source():
    pts = [
        point(B.LOCAL_SOURCE, 1, 17, 1000),
        point(B.LOCAL_SOURCE, 2, 17, 900),
        point(B.ICARM_SOURCE, 3, 17, 800),
        point(B.ICARM_SOURCE, 4, 17, 850),
    ]
    best = B.best_per_rank(pts, "conductor")
    assert {(p.source, p.source_id) for p in best} == {
        (B.LOCAL_SOURCE, "2"),
        (B.ICARM_SOURCE, "3"),
    }


def test_record_frontier_drops_rank_column_beaten_by_higher_rank():
    pts = [
        point(B.LOCAL_SOURCE, 1, 17, 1000),
        point(B.LOCAL_SOURCE, 2, 18, 900),
        point(B.LOCAL_SOURCE, 3, 19, 950),
    ]
    front = B.record_frontier(pts, "conductor")
    # rank 17 is beaten by rank 18; rank 18 and the highest-rank point remain records.
    assert {(p.rank_lower, p.source_id) for p in front} == {(18, "2"), (19, "3")}


def test_best_at_or_above_threshold():
    pts = [
        point(B.LOCAL_SOURCE, 1, 17, 1000),
        point(B.LOCAL_SOURCE, 2, 20, 700),
        point(B.ICARM_SOURCE, 3, 20, 600),
    ]
    best = B.best_at_or_above(
        pts, "conductor", min_rank=17, source=B.LOCAL_SOURCE
    )
    assert best.source_id == "2"


def test_local_loader_reads_stored_exact_torsion_label():
    conn = db()
    conn.execute(
        """INSERT INTO curves(
            id,family,parameter,conductor,discriminant,
            exact_rank,descent_lower,generic_lower,torsion_label,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (7, "torsion_family", "7", "700", "-900", None, 20, 0, "C5", "now"),
    )
    rows = B.load_local_points(conn, min_rank=20, max_rank=20)
    assert len(rows) == 1
    assert rows[0].torsion_label == "C5"


def test_icarm_torsion_labels_use_source_invariant_factors():
    assert B.icarm_torsion_label('{"torsion":[]}') == "Trivial"
    assert B.icarm_torsion_label('{"torsion":[5]}') == "C5"
    assert B.icarm_torsion_label('{"torsion":[2,8]}') == "C2 × C8"
    assert B.icarm_torsion_label('{"rank_lower_bound":20}') is None
    assert B.icarm_torsion_label("not-json") is None


def test_torsion_groups_and_filter_keep_unknown_explicit():
    pts = [
        point(B.LOCAL_SOURCE, 1, 17, 1000),
        point(B.LOCAL_SOURCE, 2, 18, 900),
        point(B.ICARM_SOURCE, 3, 19, 800),
        point(B.ICARM_SOURCE, 4, 20, 700),
    ]
    pts[0] = B.ChartPoint(**{**pts[0].__dict__, "torsion_label": "C5"})
    pts[1] = B.ChartPoint(**{**pts[1].__dict__, "torsion_label": None})
    pts[2] = B.ChartPoint(**{**pts[2].__dict__, "torsion_label": "C2 × C4"})
    pts[3] = B.ChartPoint(**{**pts[3].__dict__, "torsion_label": "C5"})

    assert B.torsion_groups(pts) == ["C5", "C2 × C4"]
    assert [p.source_id for p in B.filter_torsion(pts, "C5")] == ["1", "4"]
    assert B.torsion_metadata_counts(pts) == (3, 1)
    assert len(B.filter_torsion(pts, None)) == 4


def test_loaders_tolerate_legacy_schema_without_torsion_columns():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE curves (
            id INTEGER PRIMARY KEY, family TEXT, parameter TEXT, conductor TEXT,
            discriminant TEXT, exact_rank INTEGER, descent_lower INTEGER,
            generic_lower INTEGER, updated_at TEXT
        );
        CREATE TABLE external_curves (
            source TEXT, source_id TEXT, rank_lower_bound INTEGER, conductor TEXT,
            discriminant TEXT, naive_height TEXT, faltings_height TEXT,
            source_url TEXT, submitter TEXT, source_updated_at TEXT, active INTEGER
        );
        """
    )
    conn.execute(
        "INSERT INTO curves VALUES(?,?,?,?,?,?,?,?,?)",
        (1, "legacy", "1", "10", "-20", None, 17, 0, "now"),
    )
    conn.execute(
        "INSERT INTO external_curves VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        ("icarm", "1", 17, "20", "-30", None, None, None, None, None, 1),
    )
    assert B.load_local_points(conn, min_rank=17, max_rank=17)[0].torsion_label is None
    assert B.load_icarm_points(conn, min_rank=17, max_rank=17)[0].torsion_label is None
