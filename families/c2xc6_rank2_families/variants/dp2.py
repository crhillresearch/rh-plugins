"""Dujella–Peral II C2 x C6 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 2
historical_generic_rank_lower = 2
CONTROL_PARAMETER = QQ("17")
VARIANT_ID = "dp2"


def name():
    return "C2 x C6 rank-2 · Dujella–Peral II"


def _a_raw(u):
    return (
        -3359232 + 2239488*u + 6905088*u**2 - 11695104*u**3
        + 6925824*u**4 - 2494368*u**5 + 3007512*u**6 - 3509088*u**7
        + 2015437*u**8 - 584848*u**9 + 83542*u**10 - 11548*u**11
        + 5344*u**12 - 1504*u**13 + 148*u**14 + 8*u**15 - 2*u**16
    )


def _b_raw(u):
    return (
        (u-3)**3*(u-2)**3*(u+1)**3*(u+6)**3
        *(36-60*u+43*u**2-10*u**3+u**4)
        *(36-24*u+10*u**2-4*u**3+u**4)**3
        *(36+48*u-56*u**2+8*u**3+u**4)
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
        (u-3)**2*(u-2)**2*(u+1)**2*(u+6)**2*(u**2-8*u+6)**2
        *(36+48*u-56*u**2+8*u**3+u**4),
        QQ(1)/4*(u-3)*(u-2)*(u+1)*(u+6)
        *(u**4+8*u**3-56*u**2+48*u+36)
        *(2*u**4-14*u**3+53*u**2-84*u+72)**2,
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
        raise ArithmeticError(f"singular Dujella–Peral II specialization u={u}")
    A = a_coeff(u)
    B = b_coeff(u)
    out = []
    for xx in _x_sections(u):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 2 or any(P.is_zero() for P in out):
        raise ArithmeticError("Dujella–Peral II did not produce two nonzero sections")
    return out


def construction_check(u=CONTROL_PARAMETER):
    u = QQ(u)
    E = curve(u)
    if E is None:
        raise ArithmeticError(f"undefined Dujella–Peral II specialization u={u}")
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
        raise RuntimeError("Dujella–Peral II control specialization is singular")
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
        "certificate_version": "c2xc6-rank2-dp2-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 2,
        },
    }
