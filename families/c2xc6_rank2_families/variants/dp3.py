"""Dujella–Peral III C2 x C6 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 2
historical_generic_rank_lower = 2
CONTROL_PARAMETER = QQ("22")
VARIANT_ID = "dp3"


def name():
    return "C2 x C6 rank-2 · Dujella–Peral III"


def _a_raw(u):
    return (
        u**16 - 96*u**15 - 26496*u**14 + 11975040*u**13 - 1167338304*u**12
        + 57597516288*u**11 - 1783699937280*u**10 + 38257769207808*u**9
        - 597067735693824*u**8 + 6886398457405440*u**7
        - 57791877967872000*u**6 + 335908714991616000*u**5
        - 1225425058007040000*u**4 + 2262765238272000000*u**3
        - 901187887104000000*u**2 - 587731230720000000*u
        + 1101996057600000000
    )


def _b_raw(u):
    return (
        5971968*(u-15)**3*(u-12)**3*u**3
        *(32400-17280*u+2232*u**2-96*u**3+u**4)**3
        *(32400-4320*u+288*u**2-24*u**3+u**4)
        *(32400+34560*u-5544*u**2+192*u**3+u**4)
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
        18432*(u-15)**2*(u-12)**2*u**2
        *(u**4-96*u**3+2232*u**2-17280*u+32400)**3
        *(u**4-24*u**3+288*u**2-4320*u+32400)
        /(u**2-24*u+180)**4,
        -15552*(u-15)**2*(u-12)**2*u**2*(u**2-24*u+180)**2
        *(u**4+192*u**3-5544*u**2+34560*u+32400),
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
        raise ArithmeticError(f"singular Dujella–Peral III specialization u={u}")
    A = a_coeff(u)
    B = b_coeff(u)
    out = []
    for xx in _x_sections(u):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 2 or any(P.is_zero() for P in out):
        raise ArithmeticError("Dujella–Peral III did not produce two nonzero sections")
    return out


def construction_check(u=CONTROL_PARAMETER):
    u = QQ(u)
    E = curve(u)
    if E is None:
        raise ArithmeticError(f"undefined Dujella–Peral III specialization u={u}")
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
        raise RuntimeError("Dujella–Peral III control specialization is singular")
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
        "certificate_version": "c2xc6-rank2-dp3-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 2,
        },
    }


def source_base_change(u):
    """Paper §8.3 base change w=(u^2-30u+180)/(3(u^2-180))."""
    u = QQ(u)
    return (u**2 - 30*u + 180) / (3*(u**2 - 180))


def source_rank1_coefficients(w):
    """The printed §8.3 rank-1 coefficients before the second quadratic section."""
    w = QQ(w)
    a = 121 - 2136*w**2 - 5184*w**4 + 273024*w**6 - 1223424*w**8
    b = 128*(3*w-1)**3*(3*w+1)**3*(1+6*w**2)*(24*w**2-1)**3*(48*w**2-7)
    return a, b


def source_reconstruction_check(u):
    """Verify the cleared §8.3 model directly from the printed rank-1 source."""
    u = QQ(u)
    w = source_base_change(u)
    a, b = source_rank1_coefficients(w)
    D = u**2 - 180
    scale = QQ(9) * D**4 / QQ(25)
    return a_coeff(u) == a*scale**2 and b_coeff(u) == b*scale**4
