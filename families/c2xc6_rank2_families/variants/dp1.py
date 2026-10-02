"""Dujella–Peral I C2 x C6 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 2
historical_generic_rank_lower = 2
CONTROL_PARAMETER = QQ("15")
VARIANT_ID = "dp1"


def name():
    return "C2 x C6 rank-2 · Dujella–Peral I"


def _a_raw(u):
    return (
        1475789056 - 6324810240*u + 12303261824*u**2 - 14934296832*u**3
        + 12836014912*u**4 - 8279778528*u**5 + 4113507272*u**6
        - 1590783936*u**7 + 480725533*u**8 - 113627424*u**9
        + 20987282*u**10 - 3017412*u**11 + 334132*u**12
        - 27768*u**13 + 1634*u**14 - 60*u**15 + u**16
    )


def _b_raw(u):
    return (
        -27*(u-4)**3*u**3*(2*u-7)**3
        *(196-336*u+152*u**2-24*u**3+u**4)
        *(196-168*u+62*u**2-12*u**3+u**4)**3
        *(392-420*u+169*u**2-30*u**3+2*u**4)
    )


def a_coeff(u):
    u = QQ(u)
    return QQ(_a_raw(u))


def b_coeff(u):
    u = QQ(u)
    return QQ(_b_raw(u))


def _x_sections(u):
    u = QQ(u)
    return [
        -27*(u-4)**2*u**2*(2*u-7)**2*(14-8*u+u**2)**2
        *(196-336*u+152*u**2-24*u**3+u**4),
        -QQ(27)/4*(u-4)**2*u**2*(2*u-7)**2*(u**2-7*u+14)**2
        *(u**4-24*u**3+152*u**2-336*u+196),
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


def curve(u):
    try:
        u = QQ(u)
        E = EllipticCurve(QQ, [0, a_coeff(u), 0, b_coeff(u), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r0, p0):
    try:
        p = int(p0)
        if p == 2:
            return None
        K = GF(p)
        u = K(int(r0))
        E = EllipticCurve(K, [0, _a_raw(u), 0, _b_raw(u), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(u):
    u = QQ(u)
    E = curve(u)
    if E is None:
        raise ArithmeticError(f"singular Dujella–Peral I specialization u={u}")
    A = a_coeff(u)
    B = b_coeff(u)
    out = []
    for xx in _x_sections(u):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 2 or any(P.is_zero() for P in out):
        raise ArithmeticError("Dujella–Peral I did not produce two nonzero sections")
    return out


def construction_check(u=CONTROL_PARAMETER):
    u = QQ(u)
    E = curve(u)
    if E is None:
        raise ArithmeticError(f"undefined Dujella–Peral I specialization u={u}")
    points = generic_section_points(u)
    torsion = E.torsion_subgroup().invariants()
    return {
        "variant": VARIANT_ID,
        "parameter": str(u),
        "sections": len(points),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in points}),
        "torsion_invariants": [int(x) for x in torsion],
        "a_invariants": [str(a) for a in E.a_invariants()],
    }


def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate

    E = curve(CONTROL_PARAMETER)
    if E is None:
        raise RuntimeError("Dujella–Peral I control specialization is singular")
    points = generic_section_points(CONTROL_PARAMETER)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=180,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    return {
        "verified": bool(exact.get("independent") is True and lower >= 2),
        "lower_bound": lower,
        "method": "two published full free generators + Rank Hunter exact independence certificate",
        "certificate_version": "c2xc6-rank2-dp1-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 2,
        },
    }
