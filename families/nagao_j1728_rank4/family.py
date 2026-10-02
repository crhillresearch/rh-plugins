"""Nagao's j=1728 family with generic rank lower bound 4.

Primary source:
Koh-ichi Nagao, "On the rank of elliptic curve y^2 = x^3 - kx",
Kobe J. Math. 11 (1994), 205-210.

Theorem 1 proves infinitely many pairwise non-Q-isomorphic curves with rank
at least 4.  The paper does not prove exact generic rank 4.
"""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ

generic_rank = 4
historical_generic_rank_lower = 4
CONTROL_PARAMETER = QQ(3)
parameter_symmetry = "sign"


def name():
    return "Nagao j=1728 rank >=4 twist family"


def _a_raw(t):
    return (
        2*t**7 + t**6 + 20*t**5 - 17*t**4
        + 2*t**3 - 17*t**2 + 8*t + 1
    ) / 64


def _b_raw(t):
    return (
        t**7 - 8*t**6 - 17*t**5 - 2*t**4
        - 17*t**3 - 20*t**2 + t - 2
    ) / 64


def _c_raw(t):
    return (
        2*t**7 - t**6 + 20*t**5 + 17*t**4
        + 2*t**3 + 17*t**2 + 8*t - 1
    ) / 64


def _d_raw(t):
    return (
        -t**7 - 8*t**6 + 17*t**5 - 2*t**4
        + 17*t**3 - 20*t**2 - t - 2
    ) / 64


def _k_raw(t):
    a = _a_raw(t)
    b = _b_raw(t)
    return a**4 + b**4


def k_coeff(t):
    t = QQ(t)
    return QQ(_k_raw(t))


def factorized_k(t):
    """Nagao's equation (2.1), including the exact 2^24 denominator."""
    t = QQ(t)
    return QQ(
        (t**4 + 1)
        * (t**8 - 4*t**6 + 134*t**4 - 4*t**2 + 1)
        * (t**8 + 60*t**6 + 134*t**4 + 60*t**2 + 1)
        * (17*t**8 + 28*t**6 + 166*t**4 + 28*t**2 + 17)
    ) / (2**24)


def source_identity_check(t):
    t = QQ(t)
    a = QQ(_a_raw(t))
    b = QQ(_b_raw(t))
    c = QQ(_c_raw(t))
    d = QQ(_d_raw(t))
    k = k_coeff(t)
    return {
        "equal_biquadrates": a**4 + b**4 == c**4 + d**4,
        "factorization": k == factorized_k(t),
    }


def curve(t):
    try:
        t = QQ(t)
        k = k_coeff(t)
        if k == 0:
            return None
        E = EllipticCurve(QQ, [0, 0, 0, -k, 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r0, p0):
    try:
        p = int(p0)
        if p == 2:
            return None
        K = GF(p)
        t = K(int(r0))
        inv64 = K(64)**(-1)
        a = (
            2*t**7 + t**6 + 20*t**5 - 17*t**4
            + 2*t**3 - 17*t**2 + 8*t + 1
        ) * inv64
        b = (
            t**7 - 8*t**6 - 17*t**5 - 2*t**4
            - 17*t**3 - 20*t**2 + t - 2
        ) * inv64
        k = a**4 + b**4
        if k == 0:
            return None
        E = EllipticCurve(K, [0, 0, 0, -k, 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(t):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"singular Nagao specialization t={t}")
    a = QQ(_a_raw(t))
    b = QQ(_b_raw(t))
    c = QQ(_c_raw(t))
    d = QQ(_d_raw(t))
    if a**4 + b**4 != c**4 + d**4:
        raise ArithmeticError("Nagao equal-biquadrate identity failed")
    points = [
        E(-a**2, a*b**2),
        E(-b**2, b*a**2),
        E(-c**2, c*d**2),
        E(-d**2, d*c**2),
    ]
    if any(P.is_zero() for P in points):
        raise ArithmeticError("Nagao construction produced a zero section")
    return points


def construction_check(t=CONTROL_PARAMETER):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"undefined Nagao specialization t={t}")
    points = generic_section_points(t)
    ident = source_identity_check(t)
    return {
        "parameter": str(t),
        "a": str(QQ(_a_raw(t))),
        "b": str(QQ(_b_raw(t))),
        "c": str(QQ(_c_raw(t))),
        "d": str(QQ(_d_raw(t))),
        "k": str(k_coeff(t)),
        "factorization_ok": bool(ident["factorization"]),
        "equal_biquadrates": bool(ident["equal_biquadrates"]),
        "sections": len(points),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in points}),
        "torsion_invariants": [int(v) for v in E.torsion_subgroup().invariants()],
        "j_invariant": str(E.j_invariant()),
        "x_coordinates": [str(QQ(P[0])) for P in points],
    }


def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate

    E = curve(CONTROL_PARAMETER)
    if E is None:
        raise RuntimeError("Nagao control t=3 is singular")
    points = generic_section_points(CONTROL_PARAMETER)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=240,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    return {
        "verified": bool(exact.get("independent") is True and lower >= 4),
        "lower_bound": lower,
        "method": "four Nagao sections + Rank Hunter exact independence certificate at t=3",
        "certificate_version": "nagao-j1728-rank4-generic-lower-v0.1.0",
        "details": {
            "control_parameter": "3",
            "section_count": len(points),
            "specialization_certificate": exact,
            "generic_claim": "rank >= 4",
            "exact_generic_rank_claimed": False,
        },
    }
