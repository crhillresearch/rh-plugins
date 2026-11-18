from sage.all import QQ

import channel_engine
from channel_engine import search


def pairs(result):
    return {(record["x"], record["y"]) for record in result["points"]}


def test_control_point_found_without_seed():
    result = search(4, x_abs_max=800, z_max=1, max_points=1000)
    assert result["status"] == "completed"
    assert result["coverage"] == "bounded_complete"
    assert result["factor"] == {"complete": True, "primes": [2, 3, 5]}
    assert {("800", "448800"), ("800", "-448800")} <= pairs(result)
    assert any(r["d"] == 2 and r["k"] == 20 and r["Z"] == 1 for r in result["points"])


def test_complete_squareclasses_match_independent_grid():
    for t in (2, 3, 4, QQ(5)/2):
        kwargs = {"x_abs_max": 120, "z_max": 2, "max_points": 1000,
                  "max_candidates": 10000, "run_timeout": 30}
        channels = search(t, **kwargs)
        grid = search(t, generator="grid_control", **kwargs)
        assert channels["coverage"] == "bounded_complete"
        assert grid["coverage"] == "grid_bounded_complete"
        assert pairs(channels) == pairs(grid)


def test_caps_and_factor_failure_never_claim_exhaustion(monkeypatch):
    assert search(4, x_abs_max=800, z_max=1, k_max=1, max_points=1000)["status"] == "partial"
    assert search(4, x_abs_max=800, z_max=1, max_candidates=1)["status"] == "partial"
    monkeypatch.setattr(channel_engine, "factor_prime_support", lambda *_: {
        "complete": False, "primes": [], "reason": "factor_timeout"})
    stopped = search(4, x_abs_max=20, z_max=1)
    assert stopped["status"] == "inconclusive"
    assert stopped["coverage"] == "bounded_partial"
    fallback = search(4, x_abs_max=20, z_max=1, require_full_factorization=False)
    assert fallback["status"] == "partial"
    assert fallback["coverage"] == "bounded_partial"


def test_modular_sieve_keeps_true_squares_and_torsion():
    with_sieve = search(4, x_abs_max=800, z_max=1, max_points=1000)
    no_sieve = search(4, x_abs_max=800, z_max=1, max_points=1000, modular_sieve=False)
    assert pairs(with_sieve) == pairs(no_sieve)
    assert ("-50625", "0") in pairs(search(4, x_abs_max=50625, z_max=1,
                                            max_points=1000, max_candidates=100000))


def test_checkpoint_resumes_after_budget_and_cancellation():
    state = {}

    def save(cursor):
        state.clear()
        state.update(cursor)

    first = search(4, x_abs_max=800, z_max=1, max_points=1000,
                   max_candidates=1, checkpoint=save)
    assert first["status"] == "partial"
    assert first["reason"] == "candidate_budget"
    resumed = search(4, x_abs_max=800, z_max=1, max_points=1000,
                     max_candidates=10000, resume=state)
    assert resumed["coverage"] == "bounded_complete"
    assert ("800", "448800") in pairs(resumed)
    cancelled = search(4, x_abs_max=800, z_max=1, cancelled=lambda: True)
    assert cancelled["status"] == "partial"
    assert cancelled["reason"] == "cancelled"
