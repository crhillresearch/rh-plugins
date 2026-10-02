"""Dujella-Peral infinite rational-Diophantine-triple family with rank >= 7.

Primary source:
A. Dujella and J. C. Peral,
"High rank elliptic curves induced by rational Diophantine triples",
Glasnik Matematicki 55(2) (2020), 237-252, arXiv:2005.10706.

The rank-7 locus is not a rational line.  It is the genus-1 quartic

    z^2 = 54*w^4 + 2736*w^3 + 66592*w^2 + 2987712*w + 64393056.

For an exact rational point (w,z) on this quartic, condition (8) of the paper
gives a rational w2 and transports the sixth point from curve (11) to curve
(12), producing seven independent sections over the elliptic base function
field.  Rank Hunter uses the positive rational square root z for a deterministic
specialization representative; changing z to -z selects the conjugate w2 root.

The paper proves only generic rank >= 7 for this infinite family; exact generic
rank 7 is NOT claimed here.
"""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank = 7
historical_generic_rank_lower = 7
CONTROL_PARAMETER = QQ(26)


def name():
    return "Dujella-Peral rational Diophantine triple rank >= 7"


def _base_quartic(w):
    return (
        54*w**4
        + 2736*w**3
        + 66592*w**2
        + 2987712*w
        + 64393056
    )


def _condition8(w2, w3):
    return (
        w2**2*w3**2
        + 72*w2**2*w3
        + 88*w2*w3**2
        + 1820*w2**2
        - 1520*w3**2
        - 96096*w2
        - 65664*w3
        - 995904
    )


def _sqrt_qq(value):
    value = QQ(value)
    if value < 0:
        raise ArithmeticError("expected rational square, got negative value")
    n = ZZ(value.numerator())
    d = ZZ(value.denominator())
    if not n.is_square() or not d.is_square():
        raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt()) / QQ(d.sqrt())


def rank7_base_lift(w3):
    """Return the deterministic exact (w3,z,w2) point on the paper's rank-7 base.

    The discriminant of condition (8), viewed as a quadratic in w2, is exactly
    256 times the quartic in equation (10).  The minus branch with z >= 0 sends
    the paper control w3=26 to w2=-76/3.
    """
    w3 = QQ(w3)
    z = _sqrt_qq(_base_quartic(w3))
    den = w3**2 + 72*w3 + 1820
    if den == 0:
        raise ArithmeticError("rank-7 base lift has zero denominator")
    w2 = (48048 - 44*w3**2 - 8*z) / den
    if _condition8(w2, w3) != 0:
        raise ArithmeticError("rank-7 base lift failed paper condition (8)")
    return {
        "w3": w3,
        "z": z,
        "w2": QQ(w2),
    }


def _a63_raw(w):
    return (
        -13122*w**16
        - 7348320*w**15
        - 1570137696*w**14
        - 206172584064*w**13
        - 19541430237312*w**12
        - 1402008391816704*w**11
        - 77606011598363136*w**10
        - 3410103604914358272*w**9
        - 123219415654113963008*w**8
        - 3723833136566479233024*w**7
        - 92542375014630498607104*w**6
        - 1825654232153731017572352*w**5
        - 27787335201034030779236352*w**4
        - 320143070559304939026382848*w**3
        - 2662401630093588063697895424*w**2
        - 13606503227295711027839631360*w
        - 26532681293226636504287281152
    )


def _F1(w):
    return w**4 + 72*w**3 + 8504*w**2 + 550368*w + 10732176


def _F2(w):
    return 3*w**4 + 144*w**3 + 3160*w**2 + 157248*w + 3577392


def _F3(w):
    return 3*w**4 + 1152*w**3 + 71144*w**2 + 1257984*w + 3577392


def _F4(w):
    return 9*w**4 + 504*w**3 + 8504*w**2 + 78624*w + 1192464


def _F5(w):
    return 9*w**4 + 576*w**3 + 19192*w**2 + 628992*w + 10732176


def _F6(w):
    return 9*w**4 + 1152*w**3 + 58040*w**2 + 1257984*w + 10732176


def _F7(w):
    return 9*w**4 + 2736*w**3 + 164872*w**2 + 2987712*w + 10732176


def _H(w):
    return 171*w**4 + 16704*w**3 + 753128*w**2 + 18240768*w + 203911344


def _b63_raw(w):
    return (
        81
        * _F1(w)
        * _F2(w)
        * _F3(w)
        * _F4(w)
        * _F5(w)**2
        * _F6(w)
        * _F7(w)
    )


def _a62_raw(w):
    return (
        79573*w**16
        + 2281840*w**15
        - 791687936*w**14
        - 34844285696*w**13
        + 3065917324288*w**12
        + 556971294060544*w**11
        - 64165839736733696*w**10
        + 3360211454234263552*w**9
        - 130403990149389221888*w**8
        + 3064512846261648359424*w**7
        - 53369552205989831245824*w**6
        + 422490869190468915167232*w**5
        + 2120995723090424777146368*w**4
        - 21983951517250398896259072*w**3
        - 455536370311599498486349824*w**2
        + 1197427029434259336824094720*w
        + 38082411231292796255084740608
    )


def _x26(w):
    return (
        324
        * (w**2 - 912)**2
        * (w**4 + 352*w**3 - 50720*w**2 + 321024*w + 831744)
        * (7*w**4 - 176*w**3 + 11680*w**2 - 160512*w + 5822208)
        * (7*w**4 + 352*w**3 - 61664*w**2 + 321024*w + 5822208)
    )


def a_coeff(w3):
    w3 = QQ(w3)
    return QQ(_a63_raw(w3))


def b_coeff(w3):
    w3 = QQ(w3)
    return QQ(_b63_raw(w3))


def _six_parent_x(w):
    return [
        9*_F2(w)*_F3(w)*_F5(w)**2,
        9*_F2(w)*_F3(w)*_F5(w)*_F7(w),
        QQ(1)/49*_F2(w)*_F3(w)*_H(w)**2,
        27*_F1(w)*_F2(w)*_F4(w)*_F7(w),
        27*(w**2 - 1092)**2*_F3(w)*_F6(w)*_F7(w),
        81*(w**2 + 54*w + 1092)**2*_F2(w)*_F3(w)*_F6(w),
    ]


def _seven_x(w3):
    lift = rank7_base_lift(w3)
    w3 = lift["w3"]
    w2 = lift["w2"]
    a63 = QQ(_a63_raw(w3))
    a62 = QQ(_a62_raw(w2))
    if a62 == 0:
        raise ArithmeticError("paper curve (11) has zero a62 at lifted parameter")
    out = list(_six_parent_x(w3))
    out.append(QQ(_x26(w2)) * a63 / a62)
    return out


def curve(w3):
    """Return curve (12) only on the exact rational rank-7 base locus."""
    try:
        w3 = QQ(w3)
        rank7_base_lift(w3)
        E = EllipticCurve(QQ, [0, a_coeff(w3), 0, b_coeff(w3), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r0, p0):
    """Local rank-7 base sieve plus curve (12) over F_p.

    Valid rational rank-7 parameters satisfy the quartic square condition at
    every good prime.  Returning None on nonsquare residues makes Nagao
    candidate generation double as a local-solubility sieve.
    """
    try:
        p = int(p0)
        if p == 2:
            return None
        K = GF(p)
        w = K(int(r0))
        q = _base_quartic(w)
        if not q.is_square():
            return None
        E = EllipticCurve(K, [0, _a63_raw(w), 0, _b63_raw(w), 0])
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(w3):
    w3 = QQ(w3)
    E = curve(w3)
    if E is None:
        raise ArithmeticError(
            f"w3={w3} is not an exact rational point of the rank-7 base quartic"
        )
    A = a_coeff(w3)
    B = b_coeff(w3)
    out = []
    for xx in _seven_x(w3):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 7 or any(P.is_zero() for P in out):
        raise ArithmeticError("rank-7 construction did not produce seven nonzero sections")
    return out


def construction_check(w3=CONTROL_PARAMETER):
    w3 = QQ(w3)
    lift = rank7_base_lift(w3)
    E = curve(w3)
    if E is None:
        raise ArithmeticError(f"undefined rank-7 specialization w3={w3}")
    points = generic_section_points(w3)
    return {
        "parameter": str(w3),
        "base_square_root": str(lift["z"]),
        "lifted_w2": str(lift["w2"]),
        "condition8": str(_condition8(lift["w2"], w3)),
        "sections": len(points),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in points}),
        "torsion_invariants": [int(v) for v in E.torsion_subgroup().invariants()],
        "a_invariants": [str(a) for a in E.a_invariants()],
        "x_coordinates": [str(QQ(P[0])) for P in points],
    }


def validate_generic_rank_claim():
    """Verify the seven sections on the genus-1 base by exact specialization.

    The source proves an infinite family with rank >= 7, not exact generic rank
    7.  The seven sections live over the quartic base function field.  Exact
    independence at the good base point (w2,w3)=(-76/3,26) rules out a generic
    integral relation among these seven sections.
    """
    from rank42.exact_lb import run_exact_certificate

    E = curve(CONTROL_PARAMETER)
    if E is None:
        raise RuntimeError("rank-7 control w3=26 is unavailable")
    points = generic_section_points(CONTROL_PARAMETER)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=360,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    return {
        "verified": bool(exact.get("independent") is True and lower >= 7),
        "lower_bound": lower,
        "method": (
            "seven published/transported sections on the genus-1 rank-7 base "
            "+ Rank Hunter exact independence certificate at w3=26"
        ),
        "certificate_version": "rational-diophantine-rank7-base-v0.1.0",
        "details": {
            "control_parameter": "26",
            "control_w2": "-76/3",
            "control_base_square_root": "16120",
            "section_count": len(points),
            "specialization_certificate": exact,
            "generic_claim": "rank >= 7 over the genus-1 base function field",
            "exact_generic_rank_claimed": False,
        },
    }
