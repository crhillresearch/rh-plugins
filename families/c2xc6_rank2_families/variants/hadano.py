"""Hadano / Dujella–Peral IV C2 x C6 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 2
historical_generic_rank_lower = 2
CONTROL_PARAMETER = QQ("19")
VARIANT_ID = "hadano"


def name():
    return "C2 x C6 rank-2 · Hadano / Dujella–Peral IV"


def _a_raw(u):
    return (
        -314928 - 7978176*u - 47134224*u**2 - 141974208*u**3
        - 263196864*u**4 - 321113808*u**5 - 259493652*u**6
        - 128609568*u**7 - 23353995*u**8 + 16908960*u**9
        + 16006092*u**10 + 6735888*u**11 + 1706128*u**12
        + 271104*u**13 + 27360*u**14 + 1920*u**15 + 96*u**16
    )


def _b_raw(u):
    return (
        16*(u-6)**3*u*(u+2)**3*(3*u+4)*(u**2-3)
        *(u**2+3*u+1)**3*(u**2+9*u+9)**3*(2*u**2+4*u+3)**3
        *(2*u**2+12*u+21)*(3*u**2+8*u+9)
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
        -4*(u-6)*u*(u+2)*(3*u+4)*(u**2+3*u+1)*(u**2+9*u+9)
        *(2*u**4+8*u**3+22*u**2+48*u+45)**2,
        (6-u)*(2+u)*(1+3*u+u**2)*(9+9*u+u**2)
        *(3+4*u+2*u**2)**3*(21+12*u+2*u**2)*(9+8*u+3*u**2),
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
        raise ArithmeticError(f"singular Hadano / Dujella–Peral IV specialization u={u}")
    A = a_coeff(u)
    B = b_coeff(u)
    out = []
    for xx in _x_sections(u):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 2 or any(P.is_zero() for P in out):
        raise ArithmeticError("Hadano / Dujella–Peral IV did not produce two nonzero sections")
    return out


def construction_check(u=CONTROL_PARAMETER):
    u = QQ(u)
    E = curve(u)
    if E is None:
        raise ArithmeticError(f"undefined Hadano / Dujella–Peral IV specialization u={u}")
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
        raise RuntimeError("Hadano / Dujella–Peral IV control specialization is singular")
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
        "certificate_version": "c2xc6-rank2-hadano-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 2,
        },
    }
