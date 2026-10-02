"""Kihara Z/6 rank-3 variant from Dujella-Peral-Tadic (2016)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 3
historical_generic_rank_lower = 3
CONTROL_PARAMETER = QQ("15")
VARIANT_ID = "kihara"


def name():
    return "Dujella-Peral-Tadic Z/6 rank-3 · Kihara"


def a_coeff(t):
    t = QQ(t)
    return -2*(64*t**8 - 1952*t**7 - 4652*t**6 - 10172*t**5 - 28955*t**4
        + 35602*t**3 - 56987*t**2 + 83692*t + 9604)


def b_coeff(t):
    t = QQ(t)
    return (t-7)**3*(t+2)**3*(2*t+1)**3*(4*t-7)**3*(2*t**2-91*t+98)*(4*t**2+13*t+1)


def _x_sections(t):
    t = QQ(t)
    return [
        (4*t-7)*(t-7)*(4*t**2+13*t+1)*(2*t**2-7*t+14)**2,
        (2*t+1)**2*(t+2)**2*(4*t**2+13*t+1)*(64*t**5-536*t**4+1324*t**3+224*t**2-490*t-343)**2*(t-7)*(4*t-7)/(64*t**5-8*t**4-284*t**3+44*t**2+476*t-49)**2,
        (t-7)**2*(t+2)**2*(1+2*t)**2*(-7+4*t)**2*(-7+14*t+2*t**2)**2/(-7-4*t+2*t**2)**2,
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


def curve(t):
    try:
        t = QQ(t)
        E = EllipticCurve(QQ, [0, a_coeff(t), 0, b_coeff(t), 0])
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
        # Re-evaluate the integral coefficient formulas over F_p without QQ coercion.
        A = _a_raw(t)
        B = _b_raw(t)
        E = EllipticCurve(K, [0, A, 0, B, 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def _a_raw(t):
    return -2*(64*t**8 - 1952*t**7 - 4652*t**6 - 10172*t**5 - 28955*t**4
        + 35602*t**3 - 56987*t**2 + 83692*t + 9604)


def _b_raw(t):
    return (t-7)**3*(t+2)**3*(2*t+1)**3*(4*t-7)**3*(2*t**2-91*t+98)*(4*t**2+13*t+1)


def generic_section_points(t):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"singular Kihara specialization t={t}")
    A = a_coeff(t)
    B = b_coeff(t)
    out = []
    for xx in _x_sections(t):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 3 or any(P.is_zero() for P in out):
        raise ArithmeticError("Kihara did not produce three nonzero sections")
    return out


def construction_check(t=CONTROL_PARAMETER):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"undefined Kihara specialization t={t}")
    points = generic_section_points(t)
    torsion = E.torsion_subgroup().invariants()
    return {
        "variant": VARIANT_ID,
        "parameter": str(t),
        "sections": len(points),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in points}),
        "torsion_invariants": [int(x) for x in torsion],
        "a_invariants": [str(a) for a in E.a_invariants()],
    }


def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate

    E = curve(CONTROL_PARAMETER)
    if E is None:
        raise RuntimeError("Kihara control specialization is singular")
    points = generic_section_points(CONTROL_PARAMETER)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=180,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    return {
        "verified": bool(exact.get("independent") is True and lower >= 3),
        "lower_bound": lower,
        "method": "three published free generators + Rank Hunter exact independence certificate",
        "certificate_version": "dpt-z6-kihara-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 3,
        },
    }
