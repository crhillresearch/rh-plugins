from pathlib import Path
import importlib.util
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fiber_atlas_backend", ROOT / "backend.py")
B = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = B
spec.loader.exec_module(B)


def _signal_db():
    db = _db()
    db.execute("ALTER TABLE curves ADD COLUMN bad_primes_json TEXT")
    db.execute(
        "UPDATE curves SET bad_primes_json=? WHERE id=1",
        ('{"2":{"valuation":4},"11":{"valuation":1}}',),
    )
    db.executescript(
        """
        CREATE TABLE points(
            id INTEGER PRIMARY KEY,
            curve_id INTEGER,
            exact_verified INTEGER,
            rigorous_independent INTEGER
        );
        CREATE TABLE point_discoveries(
            id INTEGER PRIMARY KEY,
            curve_id INTEGER,
            exact_verified INTEGER
        );
        CREATE TABLE quartic_searches(
            id INTEGER PRIMARY KEY,
            curve_id INTEGER,
            point_count INTEGER
        );
        CREATE TABLE covering_search_attempts(
            id INTEGER PRIMARY KEY,
            curve_id INTEGER,
            ratpoints_hits INTEGER,
            mapped_points INTEGER
        );
        """
    )
    db.executemany(
        "INSERT INTO points(id,curve_id,exact_verified,rigorous_independent) VALUES(?,?,?,?)",
        [(1, 1, 1, 1), (2, 1, 1, 0), (3, 1, 0, 0)],
    )
    db.executemany(
        "INSERT INTO point_discoveries(id,curve_id,exact_verified) VALUES(?,?,?)",
        [(1, 1, 1), (2, 1, 1), (3, 1, 0)],
    )
    db.executemany(
        "INSERT INTO quartic_searches(id,curve_id,point_count) VALUES(?,?,?)",
        [(1, 1, 2), (2, 1, 3)],
    )
    db.executemany(
        "INSERT INTO covering_search_attempts(id,curve_id,ratpoints_hits,mapped_points) VALUES(?,?,?,?)",
        [(1, 1, 5, 2), (2, 1, 1, 1)],
    )
    db.commit()
    return db


def _db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE curves(
            id INTEGER PRIMARY KEY,
            family TEXT NOT NULL,
            parameter TEXT NOT NULL,
            score REAL,
            root_number INTEGER,
            generic_lower INTEGER,
            descent_lower INTEGER,
            exact_rank INTEGER,
            plugin_id TEXT,
            plugin_version TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    rows = [
        (1, "Family A", "3/4", 11.5, -1, 4, 5, None, "family_a", "1.0", "new", "2026-10-03"),
        (2, "Family A", "5/7", 13.0, 1, 4, 6, 6, "family_a", "1.0", "done", "2026-10-03"),
        (3, "Family A", "not-rational", None, None, 4, 4, None, "family_a", "1.0", "new", "2026-10-03"),
        (4, "Family B", "-9/10", 8.0, -1, 2, 2, None, "family_b", "1.0", "new", "2026-10-03"),
    ]
    db.executemany(
        """
        INSERT INTO curves(
            id,family,parameter,score,root_number,generic_lower,descent_lower,
            exact_rank,plugin_id,plugin_version,status,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    db.commit()
    return db


def _with_baseline(records, value=4, kind="generic_lower_bound", source="test"):
    return B.apply_family_baseline(
        records,
        B.FamilyBaseline(value=value, kind=kind, source=source),
    )


def test_parse_rational_parameter_is_exact_and_reduced():
    p = B.parse_rational_parameter("-10/20")
    assert p is not None
    assert p.numerator == -1
    assert p.denominator == 2
    assert p.value.numerator == -1
    assert p.value.denominator == 2
    assert p.log_denominator > 0
    assert p.signed_log_numerator < 0


def test_non_rational_parameter_text_is_not_guessed():
    assert B.parse_rational_parameter("chart:A") is None
    assert B.parse_rational_parameter("") is None


def test_rigorous_lower_and_rank_jump_use_only_stored_fields():
    r = B.FiberRecord(
        curve_id=1,
        family="A",
        parameter="1/2",
        rational_parameter=B.parse_rational_parameter("1/2"),
        score=12.0,
        root_number=-1,
        generic_lower=4,
        descent_lower=6,
        exact_rank=None,
        plugin_id=None,
        plugin_version=None,
        status=None,
        created_at=None,
        family_baseline=4,
        family_baseline_kind="generic_lower_bound",
        family_baseline_source="test",
    )
    assert r.rigorous_lower == 6
    assert r.rank_jump == 2
    assert r.exact_known is False


def test_exact_rank_participates_in_existing_rigorous_lower_projection():
    r = B.FiberRecord(
        curve_id=2,
        family="A",
        parameter="1",
        rational_parameter=B.parse_rational_parameter("1"),
        score=None,
        root_number=1,
        generic_lower=4,
        descent_lower=5,
        exact_rank=7,
        plugin_id=None,
        plugin_version=None,
        status=None,
        created_at=None,
        family_baseline=4,
        family_baseline_kind="exact_generic_rank",
        family_baseline_source="test",
    )
    assert r.rigorous_lower == 7
    assert r.rank_jump == 3
    assert r.exact_known is True


def test_family_inventory_and_load_are_read_only():
    db = _db()
    before = db.total_changes
    inventory = B.list_families(db)
    records = B.load_family(db, "Family A")
    after = db.total_changes

    assert after == before
    assert [item.family for item in inventory] == ["Family A", "Family B"]
    assert inventory[0].count == 3
    assert inventory[0].max_rigorous_lower == 6
    assert len(records) == 3
    assert records[0].numerator == 3
    assert records[0].denominator == 4
    assert records[2].rational_parameter is None


def test_family_summary_keeps_exact_and_heuristic_counts_separate():
    db = _db()
    summary = B.family_summary(_with_baseline(B.load_family(db, "Family A")))
    assert summary["fibers"] == 3
    assert summary["rational_parameters"] == 2
    assert summary["max_rigorous_lower"] == 6
    assert summary["rank_jump_fibers"] == 2
    assert summary["baseline_excess_fibers"] == 2
    assert summary["max_baseline_excess"] == 2
    assert summary["family_baseline"] == 4
    assert summary["family_baseline_kind"] == "generic_lower_bound"
    assert summary["exact_rank_fibers"] == 1
    assert summary["root_number_known"] == 2
    assert summary["max_score"] == 13.0


def test_plottable_records_drop_only_missing_axis_values():
    db = _db()
    records = B.load_family(db, "Family A")
    plotted = B.plottable_records(records, "log_height", "score")
    assert [record.curve_id for record, _, _ in plotted] == [1, 2]


def test_picker_order_prefers_rank_jump_then_lower_then_score():
    db = _db()
    ordered = B.picker_order(_with_baseline(B.load_family(db, "Family A")))
    assert [record.curve_id for record in ordered] == [2, 1, 3]


def test_metric_values_match_stored_semantics():
    db = _db()
    base = _with_baseline(B.load_family(db, "Family A"))
    record = B.apply_search_yield_signals(
        base,
        B.load_search_yield_signals(db, "Family A"),
    )[0]
    assert B.metric_value(record, "rigorous_lower") == 5.0
    assert B.metric_value(record, "rank_jump") == 1.0
    assert B.metric_value(record, "root_number") == -1.0
    assert B.metric_value(record, "log_denominator") > 0


def test_bad_prime_parser_accepts_only_explicit_prime_slots():
    assert B.parse_bad_primes_json('[2,3,5,9]') == (2, 3, 5)
    assert B.parse_bad_primes_json('{"2":{"valuation":7},"11":{"valuation":1}}') == (2, 11)
    assert B.parse_bad_primes_json('[{"p":13,"e":2},{"prime":17,"e":1}]') == (13, 17)
    assert B.parse_bad_primes_json('{"valuation":5,"count":3}') == ()


def test_durable_search_yield_projection_is_read_only_and_curve_scoped():
    db = _signal_db()
    before = db.total_changes
    record = B.apply_search_yield_signals(
        B.load_family(db, "Family A"),
        B.load_search_yield_signals(db, "Family A"),
    )[0]
    after = db.total_changes

    assert after == before
    assert record.bad_primes == ()
    assert record.exact_points == 2
    assert record.rigorous_points == 1
    assert record.point_discovery_events == 3
    assert record.exact_discoveries == 2
    assert record.quartic_searches == 2
    assert record.quartic_hits == 5
    assert record.covering_attempts == 2
    assert record.covering_ratpoints_hits == 6
    assert record.covering_mapped_points == 3

    assert B.metric_value(record, "exact_discoveries") == 2.0
    assert B.metric_value(record, "quartic_hits") == 5.0
    assert B.metric_value(record, "covering_mapped") == 3.0
    assert B.metric_value(record, "rigorous_points") == 1.0


def test_yield_summary_and_bad_prime_fingerprint_are_descriptive_counts():
    db = _signal_db()
    records = B.apply_search_yield_signals(
        B.load_family(db, "Family A"),
        B.load_search_yield_signals(db, "Family A"),
    )
    summary = B.yield_summary(records)
    assert summary["exact_discoveries"] == 2
    assert summary["quartic_hits"] == 5
    assert summary["covering_mapped_points"] == 3
    assert summary["rigorous_points"] == 1

    records = B.apply_bad_prime_signals(
        records,
        B.load_bad_prime_signals(db, "Family A"),
    )
    fingerprint = B.bad_prime_fingerprint(records)
    assert fingerprint == [
        {"prime": 2, "fibers": 1, "share": 1.0, "metadata_fibers": 1},
        {"prime": 11, "fibers": 1, "share": 1.0, "metadata_fibers": 1},
    ]


def test_filters_preserve_unknown_metadata_until_user_restricts_it():
    db = _db()
    records = B.load_family(db, "Family A")
    assert len(B.filter_records(records)) == 3
    assert [r.curve_id for r in B.filter_records(records, root_filter="-1")] == [1]
    assert [r.curve_id for r in B.filter_records(records, exact_filter="Exact rank stored")] == [2]
    assert [r.curve_id for r in B.filter_records(records, lower_min=6)] == [2]


def test_bounded_projection_preserves_high_signal_fiber_and_caps_payload():
    rows = []
    for curve_id in range(1, 151):
        record = B.FiberRecord(
            curve_id=curve_id,
            family="A",
            parameter=str(curve_id),
            rational_parameter=B.parse_rational_parameter(str(curve_id)),
            score=float(curve_id),
            root_number=None,
            generic_lower=4,
            descent_lower=10 if curve_id == 150 else 4,
            exact_rank=None,
            plugin_id=None,
            plugin_version=None,
            status=None,
            created_at=None,
            family_baseline=4,
            family_baseline_kind="generic_lower_bound",
            family_baseline_source="test",
        )
        rows.append((record, float(curve_id), float(curve_id)))
    bounded = B.bound_plotted(rows, max_points=100)
    assert len(bounded) <= 100
    assert 150 in {record.curve_id for record, _, _ in bounded}


def test_selection_payload_is_explicit_and_reproducible():
    db = _signal_db()
    records = _with_baseline(B.load_family(db, "Family A"))[:2]
    payload = B.selection_payload(
        records,
        family="Family A",
        view="Rank jumps",
        x_metric="log_height",
        y_metric="rank_jump",
        color_metric="rigorous_lower",
        filters={"root_number": "-1"},
    )

    assert payload["source"] == "fiber_atlas"
    assert payload["kind"] == "fiber_selection"
    assert payload["family"] == "Family A"
    assert payload["curve_ids"] == [1, 2]
    assert [rec["parameter"] for rec in payload["parameters"]] == ["3/4", "5/7"]
    assert payload["parameters"][0]["family_baseline"] == 4
    assert payload["parameters"][0]["family_baseline_kind"] == "generic_lower_bound"
    assert payload["parameters"][0]["baseline_excess"] == 1
    assert payload["parameters"][0]["rank_jump"] is None
    assert payload["selection"]["view"] == "Rank jumps"
    assert payload["selection"]["axis"] == {
        "x": "log_height",
        "y": "rank_jump",
        "color": "rigorous_lower",
    }
    assert payload["selection"]["filters"] == {"root_number": "-1"}
    assert payload["selection"]["family_baseline"] == {
        "value": 4,
        "kind": "generic_lower_bound",
        "source": "test",
    }
    envelope = payload["selection"]["envelope"]
    assert envelope["fiber_count"] == 2
    assert envelope["rational_parameter_count"] == 2
    assert envelope["parameter_min"] == "5/7"
    assert envelope["parameter_max"] == "3/4"
    assert envelope["rigorous_lower_min"] == 5
    assert envelope["rigorous_lower_max"] == 6


def test_family_switch_fastpath_does_not_load_search_yield(monkeypatch):
    db = _signal_db()

    def explode(*args, **kwargs):
        raise AssertionError("ordinary family loading must not aggregate search-yield history")

    monkeypatch.setattr(B, "_signal_map", explode)
    records = B.load_family(db, "Family A")

    assert len(records) == 3
    assert all(record.exact_discoveries == 0 for record in records)
    assert all(record.quartic_hits == 0 for record in records)
    assert all(record.covering_mapped_points == 0 for record in records)


def test_large_bad_prime_screen_does_not_trial_divide_to_sqrt():
    # 2^127-1 is prime; the former sqrt(n) trial division would effectively hang.
    huge_prime = (1 << 127) - 1
    assert B._is_prime(huge_prime)
    assert not B._is_prime(huge_prime * 3)


def test_family_switch_fastpath_does_not_parse_bad_primes(monkeypatch):
    db = _signal_db()

    def explode(*args, **kwargs):
        raise AssertionError("ordinary family loading must not parse bad-prime metadata")

    monkeypatch.setattr(B, "parse_bad_primes_json", explode)
    records = B.load_family(db, "Family A")

    assert len(records) == 3
    assert all(record.bad_primes == () for record in records)


def test_bad_prime_metadata_load_is_explicit_and_attachable():
    db = _signal_db()
    records = B.load_family(db, "Family A")
    signals = B.load_bad_prime_signals(db, "Family A")
    enriched = B.apply_bad_prime_signals(records, signals)

    assert signals == {1: (2, 11)}
    assert enriched[0].bad_primes == (2, 11)
    assert enriched[1].bad_primes == ()



def _write_family_manifest(project_root, *, plugin_id="family_a", generic_rank=11, status="published lower bound"):
    plugin_dir = Path(project_root) / "plugins" / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.json").write_text(
        """{
  "schema_version": 1,
  "plugin_type": "family",
  "id": "%s",
  "name": "Test family",
  "version": "9.9.9",
  "generic_rank": %d,
  "generic_rank_status": "%s",
  "curve_family_name": "Family A"
}
""" % (plugin_id, generic_rank, status),
        encoding="utf-8",
    )


def test_rank_excess_uses_manifest_family_baseline_not_curve_generic_lower(tmp_path):
    db = _db()
    db.execute(
        "UPDATE curves SET generic_lower=11, descent_lower=11, exact_rank=NULL WHERE family='Family A'"
    )
    db.execute(
        "UPDATE curves SET generic_lower=19, descent_lower=19 WHERE id=1"
    )
    db.commit()
    _write_family_manifest(tmp_path, generic_rank=11)

    records = B.load_family(db, "Family A", project_root=tmp_path)
    first = next(record for record in records if record.curve_id == 1)

    assert first.rigorous_lower == 19
    assert first.generic_lower == 19
    assert first.family_baseline == 11
    assert first.family_baseline_kind == "generic_lower_bound"
    assert first.family_baseline_source == "plugin_manifest"
    assert first.rank_jump == 8

    summary = B.family_summary(records)
    assert summary["family_baseline"] == 11
    assert summary["max_rigorous_lower"] == 19
    assert summary["max_baseline_excess"] == 8
    assert summary["baseline_excess_fibers"] == 1


def test_no_authoritative_baseline_does_not_reuse_curve_generic_lower():
    db = _db()
    records = B.load_family(db, "Family A")
    record = records[0]

    assert record.generic_lower == 4
    assert record.rigorous_lower == 5
    assert record.family_baseline is None
    assert record.rank_jump is None


def test_exact_family_evidence_overrides_manifest_lower_bound(tmp_path):
    db = _db()
    db.execute("ALTER TABLE curves ADD COLUMN family_spec TEXT")
    db.execute("ALTER TABLE curves ADD COLUMN family_sha256 TEXT")
    db.execute(
        "UPDATE curves SET family_spec='demo_family_spec', family_sha256='sha-demo' "
        "WHERE family='Family A'"
    )
    db.execute(
        "UPDATE curves SET generic_lower=19, descent_lower=19 WHERE id=1"
    )
    db.execute(
        """
        CREATE TABLE family_evidence(
            id INTEGER PRIMARY KEY,
            family_spec TEXT,
            family_sha256 TEXT,
            generic_lower INTEGER,
            generic_upper INTEGER,
            exact_generic_rank INTEGER,
            status TEXT
        )
        """
    )
    db.execute(
        """
        INSERT INTO family_evidence(
            id,family_spec,family_sha256,generic_lower,generic_upper,
            exact_generic_rank,status
        ) VALUES(1,'demo_family_spec','sha-demo',11,11,11,'completed')
        """
    )
    db.commit()
    _write_family_manifest(tmp_path, generic_rank=10)

    records = B.load_family(db, "Family A", project_root=tmp_path)
    first = next(record for record in records if record.curve_id == 1)

    assert first.family_baseline == 11
    assert first.family_baseline_kind == "exact_generic_rank"
    assert first.family_baseline_source == "family_evidence"
    assert first.baseline_is_exact is True
    assert first.rigorous_lower == 19
    assert first.rank_jump == 8



def test_exact_baseline_selection_keeps_true_rank_jump():
    record = B.FiberRecord(
        curve_id=99,
        family="Exact Family",
        parameter="2/3",
        rational_parameter=B.parse_rational_parameter("2/3"),
        score=9.0,
        root_number=-1,
        generic_lower=7,
        descent_lower=9,
        exact_rank=None,
        plugin_id="exact_family",
        plugin_version="1.0",
        status="done",
        created_at=None,
        family_baseline=7,
        family_baseline_kind="exact_generic_rank",
        family_baseline_source="family_evidence",
    )
    payload = B.selection_payload(
        [record],
        family="Exact Family",
        view="Rank jumps",
        x_metric="log_height",
        y_metric="rank_jump",
        color_metric="rigorous_lower",
    )
    assert payload["parameters"][0]["baseline_excess"] == 2
    assert payload["parameters"][0]["rank_jump"] == 2
