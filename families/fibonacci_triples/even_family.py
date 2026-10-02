"""Rank Hunter Family module for Dujella's even-parity Fibonacci family E_+."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_math():
    path = Path(__file__).with_name("paper_math.py")
    spec = importlib.util.spec_from_file_location("rank42_fibonacci_triples_paper_math_even", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_math = _load_math()
family_parameter_for_index = _math.family_parameter_for_index
minimalist_expected_rank = _math.minimalist_expected_rank
rank_distribution_heuristic = _math.rank_distribution_heuristic
generic_rank = 1


def name():
    return "Fibonacci triples - even parity E+"


def _sage():
    from sage.all import QQ, GF, EllipticCurve
    return QQ, GF, EllipticCurve


def _curve_over(field, t):
    _, _, _, _, _, _, a, b, c = _math.even_parameters(t)
    ainvs = _math.transformed_a_invariants(a, b, c)
    _, _, EllipticCurve = _sage()
    E = EllipticCurve(field, [field(x) for x in ainvs])
    if E.discriminant() == 0:
        return None
    return E


def curve(t):
    QQ, _, _ = _sage()
    try:
        tq = QQ(t)
        if tq * tq == 5:
            return None
        return _curve_over(QQ, tq)
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r, p):
    _, GF, _ = _sage()
    try:
        F = GF(int(p))
        tr = F(int(r))
        if tr * tr == F(5):
            return None
        return _curve_over(F, tr)
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(t):
    QQ, _, _ = _sage()
    tq = QQ(t)
    E = curve(tq)
    if E is None:
        return []
    (P,) = _math.even_section_coordinates(tq)
    return [E(QQ(P[0]), QQ(P[1]))]


def validate_generic_rank_claim():
    """Certify the operational generic lower bound from one exact specialization.

    If the explicit section P were torsion over Q(T), every good specialization
    would remain torsion.  Exact non-torsion certification at T=20/9 therefore
    proves generic rank >= 1.
    """
    from rank42.exact_lb import run_exact_certificate

    control_parameter = "20/9"
    E = curve(control_parameter)
    if E is None:
        raise RuntimeError("even generic-rank control T=20/9 is singular or undefined")
    points = generic_section_points(control_parameter)
    if len(points) != 1:
        raise RuntimeError("even generic-rank control did not produce the published section")
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=120,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    verified = bool(exact.get("independent") is True and lower >= 1)
    return {
        "verified": verified,
        "lower_bound": lower,
        "method": "explicit Q(T)-section + exact specialized non-torsion certificate",
        "certificate_version": "fibonacci-triples-v0.1.3",
        "details": {
            "control_parameter": control_parameter,
            "section_count": len(points),
            "specialization_certificate": exact,
            "generic_argument": (
                "a torsion generic section would specialize to torsion at this good fiber; "
                "exact non-torsion after specialization therefore proves generic non-torsion"
            ),
        },
    }
