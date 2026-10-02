"""MacLeod Z/6 rank-3 variant from Dujella-Peral-Tadic (2016)."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 3
historical_generic_rank_lower = 3
CONTROL_PARAMETER = QQ("-30")
VARIANT_ID = "macleod"


def name():
    return "Dujella-Peral-Tadic Z/6 rank-3 · MacLeod"


def a_coeff(t):
    t = QQ(t)
    return (60637*t**16 - 9446576*t**15 + 318481560*t**14 + 7559095920*t**13
        - 673080292884*t**12 + 13070347480656*t**11 - 22695122540632*t**10
        - 1545816592882960*t**9 - 5109785850000978*t**8
        + 496074059556450416*t**7 - 4896348487968033496*t**6
        + 8785946885865627600*t**5 + 127778653981127482476*t**4
        - 861560195308301691408*t**3 + 2072099226498542082072*t**2
        - 1499601599678467324208*t - 1357666940926062868067)


def b_coeff(t):
    t = QQ(t)
    return (-(t**2-14*t-83)**3*(17*t**2-226*t-367)**3*(t**2+58*t-347)**3
        *(t**2-290*t+2017)**3
        *(445*t**8-26680*t**7+298540*t**6+7487800*t**5-100559026*t**4
          -816359048*t**3+14922867436*t**2-55316709112*t+68821828189))


def _x_sections(t):
    t = QQ(t)
    return [
        -4*(13*t**2-458*t+1021)**2*(t**2+4*t-149)**2*(t**2-290*t+2017)*(t**2+58*t-347)*(17*t**2-226*t-367)*(t**2-14*t-83),
        -9*(17*t**2-226*t-367)**3*(t**2-14*t-83)**3*(t**2-290*t+2017)*(t**2+58*t-347),
        (445*t**8-26680*t**7+298540*t**6+7487800*t**5-100559026*t**4-816359048*t**3+14922867436*t**2-55316709112*t+68821828189)*(17*t**2-226*t-367)**2*(t**2-14*t-83)**2,
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
    return (60637*t**16 - 9446576*t**15 + 318481560*t**14 + 7559095920*t**13
        - 673080292884*t**12 + 13070347480656*t**11 - 22695122540632*t**10
        - 1545816592882960*t**9 - 5109785850000978*t**8
        + 496074059556450416*t**7 - 4896348487968033496*t**6
        + 8785946885865627600*t**5 + 127778653981127482476*t**4
        - 861560195308301691408*t**3 + 2072099226498542082072*t**2
        - 1499601599678467324208*t - 1357666940926062868067)


def _b_raw(t):
    return (-(t**2-14*t-83)**3*(17*t**2-226*t-367)**3*(t**2+58*t-347)**3
        *(t**2-290*t+2017)**3
        *(445*t**8-26680*t**7+298540*t**6+7487800*t**5-100559026*t**4
          -816359048*t**3+14922867436*t**2-55316709112*t+68821828189))


def generic_section_points(t):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"singular MacLeod specialization t={t}")
    A = a_coeff(t)
    B = b_coeff(t)
    out = []
    for xx in _x_sections(t):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 3 or any(P.is_zero() for P in out):
        raise ArithmeticError("MacLeod did not produce three nonzero sections")
    return out


def construction_check(t=CONTROL_PARAMETER):
    t = QQ(t)
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"undefined MacLeod specialization t={t}")
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
        raise RuntimeError("MacLeod control specialization is singular")
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
        "certificate_version": "dpt-z6-macleod-generic-lower-v0.1.0",
        "details": {
            "variant": VARIANT_ID,
            "control_parameter": str(CONTROL_PARAMETER),
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_generic_rank": 3,
        },
    }
