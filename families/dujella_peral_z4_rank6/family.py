"""Dujella-Peral Z/4Z family of exact generic rank 6.

Published source:
A. Dujella and J. C. Peral,
"An elliptic curve over Q(u) with torsion Z/4Z and rank 6",
Rad HAZU Matematicke znanosti 28 (2024), 185-192,
arXiv:2207.08206.

We use the paper's expanded polynomial model

    y^2 = x^3 + a6(r) x^2 + b6(r) x

and the published Mordell-Weil basis P1,P2,P3,P4,R5,R6.
The paper proves exact rank 6 over Q(r). Rank Hunter operationally verifies
only the generic lower bound 6, by exact independence at the paper's good
specialization r=1.
"""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ


generic_rank = 6
historical_generic_rank_lower = 6


def name():
    return "Dujella-Peral 2024, Z/4Z generic rank 6"


def _q1(r):
    return 18*r**2 + 14*r + 16709


def _q2(r):
    return 24*r**2 - 1001*r + 14014


def _q3(r):
    return 26*r**2 + 1001*r + 12936


def _q4(r):
    return 31*r**2 - 14*r + 9702


def _q(r):
    return 72*r**4 - 182*r**3 - 13279*r**2 + 98098*r + 20917512


def a6(r):
    return 3 * (
        6637977907200*r**16
        - 327957190299648*r**15
        - 132939477324670464*r**14
        + 1334557851651990784*r**13
        + 73205200037549219248*r**12
        - 1718125119359074284768*r**11
        - 193538301177692188691736*r**10
        + 1905189555626165277886872*r**9
        + 96624855648992854220247819*r**8
        - 1026897170482503084781024008*r**7
        - 56226940796444312350911834456*r**6
        + 269042619584910197333660344992*r**5
        + 6178698341397939354226782536368*r**4
        - 60712935351132451806093801142016*r**3
        - 3259766993714464579957766495983104*r**2
        + 4334495070152077221968455683796992*r
        + 47287453161693896431461711200563200
    )


def _b_square_root(r):
    return (
        2688
        * (r - 224)
        * (r + 154)
        * (2*r - 7)
        * (32*r + 77)
        * _q1(r)
        * _q2(r)
        * _q3(r)
        * _q4(r)
        * _q(r)
    )


def b6(r):
    d = _b_square_root(r)
    return d*d


def _x_basis(r):
    q = _q(r)
    x1 = (
        -53067
        * (r - 224) * (r + 154) * (2*r - 7) * (32*r + 77)
        * _q2(r) * _q3(r) * q**2
    )
    p2 = 2424*r**4 - 12922*r**3 - 3840473*r**2 + 6964958*r + 704222904
    x2 = (
        -48
        * (r - 224) * (r + 154) * (2*r - 7) * (32*r + 77)
        * _q1(r) * _q4(r) * p2**2
    )
    p3 = 155719256 - 490490*r + 1032283*r**2 + 910*r**3 + 536*r**4
    x3 = 144 * _q1(r) * _q2(r) * _q3(r) * _q4(r) * p3**2
    p4 = 434619416 + 2648646*r - 841477*r**2 - 4914*r**3 + 1496*r**4
    x4 = 576 * _q1(r) * _q2(r) * _q3(r) * _q4(r) * p4**2

    # The paper notes that P1,P2,P3,P4,R5,R6 generate the full
    # Mordell-Weil group modulo torsion. Use R5,R6 rather than the
    # index-4 subgroup generators P5,P6.
    xR5 = (
        1344 * q * (2*r - 7)**2 * (32*r + 77)**2
        * _q1(r)**2 * (11*r**2 + 14*r + 12936)**2
    )
    dR6 = (30*r**2 - 1001*r + 17248)**2
    if dR6 == 0:
        raise ZeroDivisionError("Dujella-Peral R6 section has a pole")
    xR6 = (
        1344 * _q1(r) * _q3(r) * _q4(r) * _q2(r) * q
        * (r + 154)**2 * (32*r + 77)**2
        * (6*r**2 - 91*r + 3332)**2
        / dR6
    )
    return [x1, x2, x3, x4, xR5, xR6]


def _sqrt_qq(value):
    value = QQ(value)
    if value < 0:
        raise ArithmeticError("expected a rational square, got a negative value")
    n = ZZ(value.numerator())
    d = ZZ(value.denominator())
    if not n.is_square() or not d.is_square():
        raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt()) / QQ(d.sqrt())


def curve(r):
    try:
        r = QQ(r)
        E = EllipticCurve(QQ, [0, QQ(a6(r)), 0, QQ(b6(r)), 0])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r0, p0):
    try:
        p = int(p0)
        if p == 2:
            return None
        K = GF(p)
        r = K(int(r0))
        E = EllipticCurve(K, [0, a6(r), 0, b6(r), 0])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(r):
    r = QQ(r)
    E = curve(r)
    if E is None:
        raise ArithmeticError(f"singular Dujella-Peral specialization r={r}")
    A = QQ(a6(r))
    B = QQ(b6(r))
    out = []
    for xx in _x_basis(r):
        x = QQ(xx)
        y = _sqrt_qq(x**3 + A*x**2 + B*x)
        out.append(E(x, y))
    if len(out) != 6 or any(P.is_zero() for P in out):
        raise ArithmeticError("Dujella-Peral construction did not produce six nonzero sections")
    return out


def torsion_point(r):
    """Return the published rational point of order 4 on a good specialization."""
    r = QQ(r)
    E = curve(r)
    if E is None:
        raise ArithmeticError(f"singular Dujella-Peral specialization r={r}")
    d = -QQ(_b_square_root(r))
    s = _sqrt_qq(QQ(a6(r)) + 2*d)
    P = E(d, d*s)
    if 4*P != E(0) or 2*P == E(0):
        raise ArithmeticError("published Z/4 torsion reconstruction failed")
    return P


def construction_check(r=QQ(1)):
    r = QQ(r)
    E = curve(r)
    if E is None:
        raise ArithmeticError(f"undefined Dujella-Peral specialization r={r}")
    pts = generic_section_points(r)
    T = torsion_point(r)
    return {
        "family": name(),
        "parameter": str(r),
        "sections": len(pts),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in pts}),
        "torsion_order": int(T.order()),
        "a_invariants": [str(a) for a in E.a_invariants()],
    }


def validate_generic_rank_claim():
    """Exact-certify six published sections at the paper control r=1.

    Dujella-Peral state that the six displayed independent sections remain
    independent after specialization at r=1. Exact specialized independence
    rules out any generic integral relation, so this verifies the operational
    generic lower bound 6. The paper's separate Gusic-Tadic argument at r=13
    proves exact generic rank 6; Rank Hunter records that theorem in provenance
    rather than synthesizing a generic upper-bound object.
    """
    from rank42.exact_lb import run_exact_certificate

    control_parameter = "1"
    E = curve(control_parameter)
    if E is None:
        raise RuntimeError("Dujella-Peral control r=1 is singular")
    points = generic_section_points(control_parameter)
    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=180,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    verified = bool(exact.get("independent") is True and lower >= 6)
    return {
        "verified": verified,
        "lower_bound": lower,
        "method": (
            "six published Dujella-Peral sections + Rank Hunter exact "
            "independence certificate at r=1"
        ),
        "certificate_version": "dujella-peral-z4-rank6-generic-lower-v0.1.1",
        "details": {
            "control_parameter": control_parameter,
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_exact_rank_control": "r=13 (Gusic-Tadic injectivity)",
            "paper_generic_rank": 6,
            "generic_argument": (
                "any integral relation among the six generic sections would "
                "specialize at this good fiber; exact independence at r=1 "
                "therefore proves generic rank at least 6"
            ),
        },
    }
