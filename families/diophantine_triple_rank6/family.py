"""Dujella-Peral Diophantine-triple family with C2 x C2 torsion and exact generic rank 6.

Primary source:
A. Dujella and J. C. Peral,
"Elliptic curves induced by Diophantine triples",
RACSAM 113 (2019), 791-806, arXiv:1712.02082v2.

The original paper's equation (8) has a positive sign in x6. A later survey
reprint shows a minus sign there, but exact curve membership at v=5 confirms
the original-paper +9 sign.
"""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 6
historical_generic_rank_lower = 6
CONTROL_PARAMETER = QQ(5)


def name():
    return "Dujella-Peral Diophantine-triple rank 6"


def _gminus(v):
    return 9 - 80*v + 9*v**2


def _gplus(v):
    return 9 + 80*v + 9*v**2


def _f1(v):
    return -27 + 13*v**2


def _f2(v):
    return -13 + 27*v**2


def _p(v):
    return 9 + 8018*v**2 + 9*v**4


def _r(v):
    return 31 - 258*v**2 + 31*v**4


def _q(v):
    return 369 - 542*v**2 + 369*v**4


def _s(v):
    return 661 - 3478*v**2 + 661*v**4


def _t(v):
    return 14409 - 41564*v**2 + 400054*v**4 - 41564*v**6 + 14409*v**8


def _a_raw(v):
    return -2 * (
        130752711
        - 35202346632*v**2
        + 260292593988*v**4
        - 1337869740984*v**6
        + 1975889131370*v**8
        - 1337869740984*v**10
        + 260292593988*v**12
        - 35202346632*v**14
        + 130752711*v**16
    )


def _b_raw(v):
    return -(
        _gminus(v)
        * _gplus(v)
        * _f1(v)**2
        * _f2(v)**2
        * _p(v)
        * _r(v)
        * _q(v)
        * _t(v)
    )


def a_coeff(v):
    v = QQ(v)
    return QQ(_a_raw(v))


def b_coeff(v):
    v = QQ(v)
    return QQ(_b_raw(v))


def _x_sections(v):
    v = QQ(v)
    return [
        -QQ(1)/9 * _f1(v)**2 * _f2(v)**2 * _p(v) * _q(v),
        -QQ(1)/9 * _gminus(v) * _gplus(v) * _f1(v) * _f2(v) * _p(v) * _q(v),
        -QQ(1)/49 * _p(v) * _q(v) * _s(v)**2,
        _gminus(v) * _gplus(v) * _q(v) * _t(v),
        -441 * (1 + v**2)**2 * _f1(v) * _f2(v) * _p(v) * _r(v),
        9 * _f1(v)**2 * _f2(v)**2 * _p(v) * _r(v),
    ]


def _sqrt_qq(value):
    value = QQ(value)
    if value < 0:
        raise ArithmeticError("expected rational square, got negative value")
    n = ZZ(value.numerator())
    d = ZZ(value.denominator())
    if not n.is_square() or not d.is_square():
        raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt()) / QQ(d.sqrt())


def curve(v):
    try:
        v = QQ(v)
        E = EllipticCurve(QQ, [0, a_coeff(v), 0, b_coeff(v), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r0, p0):
    try:
        p0 = int(p0)
        if p0 == 2:
            return None
        K = GF(p0)
        v = K(int(r0))
        E = EllipticCurve(K, [0, _a_raw(v), 0, _b_raw(v), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(v):
    v = QQ(v)
    E = curve(v)
    if E is None:
        raise ArithmeticError(f"singular specialization v={v}")
    A = a_coeff(v)
    B = b_coeff(v)
    out = []
    for xx in _x_sections(v):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 6 or any(P.is_zero() for P in out):
        raise ArithmeticError("construction did not produce six nonzero sections")
    return out


def construction_check(v=CONTROL_PARAMETER):
    v = QQ(v)
    E = curve(v)
    if E is None:
        raise ArithmeticError(f"undefined specialization v={v}")
    points = generic_section_points(v)
    return {
        "parameter": str(v),
        "sections": len(points),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in points}),
        "torsion_invariants": [int(x) for x in E.torsion_subgroup().invariants()],
        "x6": str(QQ(_x_sections(v)[5])),
        "a_invariants": [str(a) for a in E.a_invariants()],
    }


def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate

    E = curve(CONTROL_PARAMETER)
    if E is None:
        raise RuntimeError("Dujella-Peral control v=5 is singular")
    points = generic_section_points(CONTROL_PARAMETER)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=300,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    return {
        "verified": bool(exact.get("independent") is True and lower >= 6),
        "lower_bound": lower,
        "method": "six published sections + Rank Hunter exact independence certificate at v=5",
        "certificate_version": "diophantine-triple-rank6-generic-lower-v0.1.0",
        "details": {
            "control_parameter": "5",
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 6,
            "paper_torsion": "C2 x C2",
        },
    }
