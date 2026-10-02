from fractions import Fraction
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fibonacci_triples_paper_math_test", ROOT / "paper_math.py")
pm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pm)


def native_rhs(a, b, c, x):
    return (a*x + 1) * (b*x + 1) * (c*x + 1)


def transformed_rhs(a, b, c, X):
    return (X + b*c) * (X + a*c) * (X + a*b)


def test_paper_q3_and_q5_positive_controls():
    assert pm.native_odd_q(3) == (Fraction(-1, 60), Fraction(13, 60))
    assert pm.native_odd_q(5) == (Fraction(-3, 1144), Fraction(89, 1144))
    for k in (3, 5):
        a, b, c = pm.fibonacci_triple(k)
        x, y = pm.native_odd_q(k)
        assert y*y == native_rhs(a, b, c, x)


def test_odd_chart_hits_fibonacci_controls():
    controls = {3: Fraction(3), 5: Fraction(5, 2), 17: Fraction(85, 38)}
    for k, T in controls.items():
        assert pm.family_parameter_for_index(k) == T
        f, ell, *_rest, a, b, c = pm.odd_parameters(T)
        assert f == pm.fibonacci(k)
        assert ell == pm.lucas(k)
        assert (a, b, c) == pm.fibonacci_triple(k)


def test_even_chart_hits_k12_control():
    T = Fraction(20, 9)
    assert pm.family_parameter_for_index(12) == T
    f, ell, *_rest, a, b, c = pm.even_parameters(T)
    assert f == 144
    assert ell == 322
    assert (a, b, c) == pm.fibonacci_triple(12)


def test_transformed_sections_are_exactly_on_curve():
    for T in (Fraction(3), Fraction(5, 2), Fraction(85, 38)):
        *_, a, b, c = pm.odd_parameters(T)
        P, Q = pm.odd_section_coordinates(T)
        for X, Y in (P, Q):
            assert Y*Y == transformed_rhs(a, b, c, X)
    T = Fraction(20, 9)
    *_, a, b, c = pm.even_parameters(T)
    (P,) = pm.even_section_coordinates(T)
    assert P[1]*P[1] == transformed_rhs(a, b, c, P[0])


def test_transformed_a_invariants_match_expansion():
    T = Fraction(3)
    *_, a, b, c = pm.odd_parameters(T)
    a1, a2, a3, a4, a6 = pm.transformed_a_invariants(a, b, c)
    assert (a1, a3) == (0, 0)
    assert a2 == a*b + a*c + b*c
    assert a4 == a*b*c*(a+b+c)
    assert a6 == (a*b*c)**2


def test_heuristic_claim_boundaries_and_densities():
    assert pm.forced_rank_baseline(2) == 1
    assert pm.forced_rank_baseline(3) == 2
    assert pm.forced_rank_baseline(1) == 1
    assert pm.minimalist_expected_rank(2, -1) == 1
    assert pm.minimalist_expected_rank(2, +1) == 2
    assert pm.minimalist_expected_rank(3, +1) == 2
    assert pm.minimalist_expected_rank(3, -1) == 3
    assert pm.rank_distribution_heuristic() == {
        1: Fraction(1, 4), 2: Fraction(1, 2), 3: Fraction(1, 4), "rank>=4": Fraction(0, 1)
    }
