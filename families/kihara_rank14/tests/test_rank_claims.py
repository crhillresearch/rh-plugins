from pathlib import Path
import sys
import pytest

pytest.importorskip("rank42.db")
from rank42.db import connect, get_curve, upsert_curve, update_curve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import rank_claims


class FakePoint:
    def __init__(self, x, y):
        self.xy = (str(x), str(y))

    def is_zero(self):
        return False

    def __getitem__(self, i):
        return self.xy[i]


class FakeCurve:
    def a_invariants(self):
        return ["0", "0", "0", "-1", "0"]


def test_exact_baseline_promotes_and_is_cached(monkeypatch, tmp_path):
    db = connect(tmp_path / "rank42.db")
    cid = upsert_curve(db, family="Kihara 2001, generic rank >=14", parameter="1")
    basis = [FakePoint(i + 1, i + 2) for i in range(14)]
    calls = []

    def fake_cert(ainvs, points, *, timeout):
        calls.append((ainvs, points, timeout))
        return {
            "status": "certified_independent", "independent": True,
            "rank_lower_bound": 14, "certificate": {"method": "test"},
        }

    monkeypatch.setattr(rank_claims, "run_exact_certificate", fake_cert)
    got = rank_claims.certify_specialized_sections(
        db, curve_id=cid, E=FakeCurve(), basis=basis, parameter="1", timeout=9,
    )
    assert got["rigorous_lower"] == 14
    assert int(get_curve(db, cid)["generic_lower"]) == 14
    n = db.execute(
        "SELECT COUNT(*) n FROM points WHERE curve_id=? AND rigorous_independent=1",
        (cid,),
    ).fetchone()["n"]
    assert int(n) == 14

    cached = rank_claims.certify_specialized_sections(
        db, curve_id=cid, E=FakeCurve(), basis=basis, parameter="1", timeout=9,
    )
    assert cached["cached"] is True
    assert len(calls) == 1


def test_legacy_unsupported_generic_lower_is_cleared(tmp_path):
    db = connect(tmp_path / "rank42.db")
    cid = upsert_curve(db, family="Kihara 2001, generic rank >=14", parameter="2")
    update_curve(db, cid, generic_lower=14)
    got = rank_claims.reconcile_specialization_lower(db, cid)
    assert got["cleared"] is True
    assert get_curve(db, cid)["generic_lower"] is None
