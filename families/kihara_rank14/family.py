"""Shoichi Kihara's 2001 elliptic curve over Q(t) of rank at least 14.

The paper constructs a genus-one quartic rather than printing a giant expanded
Weierstrass equation.  We follow that construction exactly:

    F(x) = prod_{i=1}^12 (x-b_i) = G(x)^2 - r(x),  deg r = 4,

with b_i = a_i +/- u and the published specialization p(t), q(t), u(t).
The finite-field search path uses the classical Jacobian of the binary quartic
r(x), while the rational path translates the published point P15 to x=0 and
uses the standard quartic-to-Weierstrass birational transformation.  The first
12 published points are (b_i,G(b_i)); P13 and P14 are recovered from their
published x-coordinates by exact square-root extraction.  P15 is used as the
origin, as in Kihara's theorem.

Reference:
S. Kihara, "On an elliptic curve over Q(t) of rank >= 14",
Proc. Japan Acad. Ser. A Math. Sci. 77 (2001), 50-51.
DOI 10.3792/pjaa.77.50.
"""

from __future__ import annotations

from sage.all import QQ, GF, ZZ, EllipticCurve, PolynomialRing


generic_rank = None
historical_generic_rank_lower = 14


def name():
    return "Kihara 2001, generic rank >=14"


def _pqu(t):
    p = t**2 * (8 + 3*t**2)
    q = -6 * (2 + t**2) * (4 + t**2)
    u = (
        4 * (2 + t**2)
        * (2304 + 2400*t**2 + 928*t**4 + 150*t**6 + 9*t**8)
        * (1152 + 1632*t**2 + 860*t**4 + 201*t**6 + 18*t**8)
        / t
    )
    return p, q, u


def _shifts(p, q):
    # Kihara's a_1,...,a_6 (not Weierstrass a-invariants).
    return [
        0,
        (2*p**2 + p*q + 2*q**2)**2,
        2*(p + q)**2 * (2*p**2 + p*q + q**2),
        q**2 * (4*p**2 - p*q + 4*q**2),
        p*(2*p - q) * (2*p**2 + 4*p*q + 5*q**2),
        4*p**4 + 8*p**3*q + 9*p**2*q**2 - 2*p*q**3 + 2*q**4,
    ]


def _poly_sqrt_at_infinity(F, x):
    """Return monic degree-6 G with deg(G^2-F) <= 5 for monic deg-12 F."""
    if F.degree() != 12 or F[12] != 1:
        raise ValueError("Kihara F must be monic of degree 12")
    G = x**6
    two = F.base_ring()(2)
    for k in range(11, 5, -1):
        known = (G*G)[k]
        coeff = (F[k] - known) / two
        G += coeff * x**(k - 6)
    return G


def _quartic_data(t):
    K = t.parent()
    R = PolynomialRing(K, "x")
    x = R.gen()
    p, q, u = _pqu(t)
    aa = _shifts(p, q)
    roots = [u + a for a in aa] + [-u + a for a in aa]

    # Pair the +/-u roots to reduce the polynomial work from twelve linear
    # products to six quadratics.
    F = R.one()
    for a in aa:
        F *= (x - a)**2 - u**2
    G = _poly_sqrt_at_infinity(F, x)
    r = G*G - F
    if r.degree() > 4:
        raise ArithmeticError("Kihara remainder failed to reduce to a quartic")
    return R, x, G, r, roots


def _x13(t, p, q, u):
    d = 2*p**2 + 2*p*q + 3*q**2
    return (
        (2*p**2 + 4*p*q + 5*q**2) * u
        + 8*p**6 + 28*p**5*q + 58*p**4*q**2 + 69*p**3*q**3
        + 76*p**2*q**4 + 40*p*q**5 + 22*q**6
    ) / d


def _x14(t):
    a = 1152 + 1632*t**2 + 860*t**4 + 201*t**6 + 18*t**8
    b = (
        10616832 - 18579456*t + 33619968*t**2 - 51535872*t**3
        + 45895680*t**4 - 61848576*t**5 + 35397888*t**6
        - 41945856*t**7 + 16968640*t**8 - 17591104*t**9
        + 5232272*t**10 - 4675248*t**11 + 1035180*t**12
        - 769824*t**13 + 126252*t**14 - 71874*t**15
        + 8559*t**16 - 2916*t**17 + 243*t**18
    )
    c = 2304 + 3168*t**2 + 1580*t**4 + 339*t**6 + 27*t**8
    return -4 * a * b / (t * c)


def _x15(t):
    return (
        4
        * (-48 + 24*t - 34*t**2 + 16*t**3 - 6*t**4 + 3*t**5)
        * (96 + 80*t**2 + 4*t**3 + 18*t**4 + 3*t**5)
        * (1152 + 1632*t**2 + 860*t**4 + 201*t**6 + 18*t**8)
        / t
    )


def _sqrt_qq(value):
    value = QQ(value)
    if value < 0:
        raise ArithmeticError("expected a rational square, got a negative value")
    n = ZZ(value.numerator())
    d = ZZ(value.denominator())
    if not n.is_square() or not d.is_square():
        raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt()) / QQ(d.sqrt())


def _rational_model(t):
    """Return (E, map_data, quartic_data) over QQ with P15 as origin."""
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Kihara specialization has a pole at t=0")
    R, x, G, r, roots = _quartic_data(tq)
    x0 = QQ(_x15(tq))
    y0 = _sqrt_qq(r(x0))
    if y0 == 0:
        raise ArithmeticError("P15 has y=0; quartic-origin map degenerates")

    s = R.gen()
    rt = r(s + x0)
    A, B, C, D = rt[4], rt[3], rt[2], rt[1]
    if rt[0] != y0**2:
        raise ArithmeticError("translated Kihara quartic lost P15")

    Q = 2*y0
    a1 = D/y0
    a2 = C - (D/Q)**2
    a3 = B*Q
    a4 = -A*Q**2
    a6 = a2*a4
    E = EllipticCurve(QQ, [a1, a2, a3, a4, a6])
    if E.discriminant() == 0:
        raise ArithmeticError("singular Kihara specialization")

    map_data = {
        "x0": x0, "y0": y0, "Q": Q,
        "A": A, "B": B, "C": C, "D": D,
    }
    return E, map_data, (R, x, G, r, roots)


def _map_quartic_point(E, data, xq, yq):
    x0, y0, Q = data["x0"], data["y0"], data["Q"]
    C, D = data["C"], data["D"]
    u = QQ(xq) - x0
    if u == 0:
        # P15 itself is the chosen origin.  It is not one of P1,...,P14.
        if QQ(yq) == y0:
            return E(0)
        raise ArithmeticError("quartic point above P15 x-coordinate needs the exceptional map")
    v = QQ(yq)
    X = (Q*(v + y0) + D*u) / u**2
    Y = (
        Q**3*(v + y0)
        + Q**2*(D*u + C*u**2)
        - D**2*u**2
    ) / (Q*u**3)
    return E(QQ(X), QQ(Y))


def curve(t):
    try:
        E, _, _ = _rational_model(t)
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None



def _quartic_invariants(quartic):
    a, b, c, d, e = quartic[4], quartic[3], quartic[2], quartic[1], quartic[0]
    I = 12*a*e - 3*b*d + c**2
    J = 72*a*c*e + 9*b*c*d - 27*a*d**2 - 27*b**2*e - 2*c**3
    return I, J


def screen_curve(t):
    """Cheap Jacobian model used only for rank screening.

    This avoids constructing P15, extracting rational square roots, and
    translating all published sections.  It is isomorphic to the genus-one
    quartic's Jacobian, so its Mordell-Weil rank is the rank relevant to the
    specialization screen.
    """
    try:
        tq = QQ(t)
        if tq == 0:
            return None
        _, _, _, quartic, _ = _quartic_data(tq)
        I, J = _quartic_invariants(quartic)
        E = EllipticCurve(QQ, [0, 0, 0, -27*I, -27*J])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def screen_model_name():
    return "binary_quartic_jacobian"

def curve_mod_p(r0, p0):
    """Return the Jacobian of Kihara's quartic over F_p.

    For f=a*x^4+b*x^3+c*x^2+d*x+e, the classical binary-quartic
    invariants are I=12ae-3bd+c^2 and
    J=72ace+9bcd-27ad^2-27b^2e-2c^3.  A Jacobian model is
    y^2=x^3-27Ix-27J.  We skip characteristics 2 and 3.
    """
    try:
        p = int(p0)
        if p in (2, 3):
            return None
        K = GF(p)
        t = K(int(r0))
        if t == 0:
            return None
        _, _, _, quartic, _ = _quartic_data(t)
        I, J = _quartic_invariants(quartic)
        E = EllipticCurve(K, [0, 0, 0, -27*I, -27*J])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def generic_section_points(t):
    """Specialize Kihara's fourteen published independent sections."""
    E, data, quartic_data = _rational_model(t)
    return _generic_sections_from_model(E, data, quartic_data, t)


def construction_check(t=QQ(2)):
    """Cheap exact consistency check; no height computation."""
    E = curve(t)
    if E is None:
        raise ArithmeticError(f"undefined Kihara specialization t={t}")
    pts = generic_section_points(t)
    return {
        "family": name(),
        "parameter": str(QQ(t)),
        "sections": len(pts),
        "distinct_nonzero": len({(QQ(P[0]), QQ(P[1])) for P in pts if not P.is_zero()}),
        "a_invariants": [str(a) for a in E.a_invariants()],
    }


def validate_generic_rank_claim():
    """Exact-certify Kihara's fourteen generic sections at the paper control t=2.

    Kihara's proof also specializes at t=2 and proves independence using a
    nonzero canonical-height determinant.  Rank Hunter independently runs its
    exact lower-bound certificate on those same fourteen specialized sections.
    Any integral relation over Q(t) would survive at this good specialization,
    so specialized independence proves generic rank at least 14.
    """
    from rank42.exact_lb import run_exact_certificate

    control_parameter = "2"
    E = curve(control_parameter)
    if E is None:
        raise RuntimeError("Kihara generic-rank control t=2 is singular or undefined")
    points = generic_section_points(control_parameter)
    if len(points) != 14 or any(P.is_zero() for P in points):
        raise RuntimeError(
            f"Kihara t=2 control produced {len(points)} sections; expected 14 nonzero points"
        )

    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=300,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    verified = bool(exact.get("independent") is True and lower >= 14)
    return {
        "verified": verified,
        "lower_bound": lower,
        "method": (
            "14 exact Kihara sections + Rank Hunter exact independence "
            "certificate at the paper's t=2 specialization"
        ),
        "certificate_version": "kihara2001-rank14-generic-lower-v1.2.0",
        "details": {
            "control_parameter": control_parameter,
            "section_count": len(points),
            "specialization_certificate": exact,
            "paper_proof_control": "t=2",
            "paper_height_determinant_reported": "221792776617402574.10",
            "generic_argument": (
                "any integral relation among the fourteen generic sections "
                "would specialize at this good fiber; exact independence at "
                "t=2 therefore proves generic independence"
            ),
        },
    }

# ---------------------------------------------------------------------------
# v0.4.5 direct extra-point search interface
# ---------------------------------------------------------------------------

def quartic_search_coefficients(t):
    """Return exact a0,...,a4 for Kihara's native quartic y^2=r_t(x).

    This intentionally avoids building a Weierstrass model or computing any
    heights, so a ratpoints scout can run before expensive elliptic-curve work.
    """
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Kihara specialization has a pole at t=0")
    _, _, _, r, _ = _quartic_data(tq)
    return [QQ(r[i]) for i in range(5)]


def _generic_sections_from_model(E, data, quartic_data, t):
    """Build the fourteen published sections from an already-built model."""
    _, _, G, quartic, roots = quartic_data
    tq = QQ(t)
    p, q, u = _pqu(tq)
    quartic_points = [(QQ(b), QQ(G(b))) for b in roots]
    for xx in (_x13(tq, p, q, u), _x14(tq)):
        xx = QQ(xx)
        yy = _sqrt_qq(quartic(xx))
        quartic_points.append((xx, yy))
    out = [_map_quartic_point(E, data, xx, yy) for xx, yy in quartic_points]
    if len(out) != 14:
        raise ArithmeticError("Kihara construction did not produce 14 sections")
    return out


def direct_search_bundle(t):
    """Materialize the rational Kihara model only after a quartic scout hits.

    Returns a dictionary containing the curve, fourteen known sections,
    quartic coefficients, exact map constants, and a mapper callable through
    ``map_native_quartic_point``.
    """
    tq = QQ(t)
    E, data, quartic_data = _rational_model(tq)
    basis = _generic_sections_from_model(E, data, quartic_data, tq)
    r = quartic_data[3]
    return {
        "curve": E,
        "basis": basis,
        "map_data": data,
        "quartic_coefficients": [QQ(r[i]) for i in range(5)],
    }


def native_quartic_known_points(t):
    """Return the fourteen published affine points on Kihara's quartic.

    This is intentionally cheaper than ``direct_search_bundle``: it never
    constructs a Weierstrass model or a height matrix.  It is used by the
    Mobius-chart scout to recognize already-known x-fibers before paying the
    full elliptic-curve cost.
    """
    tq = QQ(t)
    _, _, G, quartic, roots = _quartic_data(tq)
    p, q, u = _pqu(tq)
    pts = [(QQ(b), QQ(G(b))) for b in roots]
    for xx in (_x13(tq, p, q, u), _x14(tq)):
        xx = QQ(xx)
        pts.append((xx, _sqrt_qq(quartic(xx))))
    if len(pts) != 14:
        raise ArithmeticError("Kihara native quartic did not produce 14 known points")
    return pts


def native_quartic_known_x(t):
    return [P[0] for P in native_quartic_known_points(t)]


def map_native_quartic_point(bundle, x, y):
    """Map an exact affine point on y^2=r_t(x) to the bundle's E(Q)."""
    return _map_quartic_point(
        bundle["curve"], bundle["map_data"], QQ(str(x)), QQ(str(y))
    )


def native_quartic_involution_translation(bundle, t):
    """Return the exact elliptic translation attached to ``(x,y)->(x,-y)``.

    With P15 chosen as the elliptic origin, the hyperelliptic involution on
    Kihara's quartic need not be elliptic negation.  On the resulting genus-one
    group it has the form ``P |-> T - P`` for one fixed ``T``.  We determine
    ``T`` from Kihara's fourteen published affine fibres and verify *exactly*
    that every usable fibre gives the same value.

    This is a structural positive-control identity.  It does not by itself
    prove that ``T`` lies in the subgroup generated by the fourteen published
    sections.
    """
    E = bundle["curve"]
    translations = []
    for xq, yq in native_quartic_known_points(t):
        P = map_native_quartic_point(bundle, xq, yq)
        Pi = map_native_quartic_point(bundle, xq, -yq)
        translations.append(P + Pi)
    if not translations:
        raise ArithmeticError("no Kihara fibres available for involution control")
    T = translations[0]
    if any(Q != T for Q in translations[1:]):
        raise ArithmeticError(
            "Kihara quartic involution failed the exact P -> T-P consistency check"
        )
    return T


def native_quartic_involution_controls(bundle, t):
    """Return exact mapped positive-control pairs for the quartic involution.

    Each record contains a published quartic point, its opposite-sign point,
    their elliptic images, and the common translation ``T`` satisfying
    ``P_opposite = T - P_published``.  These points are useful for validating
    an exhaustive ``--include-known-fibers`` search without misclassifying the
    opposite sign of a published fibre as a newly discovered point.
    """
    T = native_quartic_involution_translation(bundle, t)
    out = []
    for index, (xq, yq) in enumerate(native_quartic_known_points(t), 1):
        P = map_native_quartic_point(bundle, xq, yq)
        Pi = map_native_quartic_point(bundle, xq, -yq)
        if Pi != T - P:
            raise ArithmeticError(
                f"Kihara quartic involution relation failed on published fibre {index}"
            )
        out.append({
            "index": index,
            "native_point": (QQ(xq), QQ(yq)),
            "published_image": P,
            "opposite_image": Pi,
            "translation": T,
        })
    return out


def covering_map_expressions_from_native(bundle, native_x="u", native_y="v"):
    """Compose the native Kihara quartic map with exact input expressions.

    ``native_x`` and ``native_y`` may themselves be rational expressions in
    the covering variables ``u,v``.  This is how a Mobius search chart is
    persisted as one exact covering map back to E.
    """
    d = bundle["map_data"]
    x0, y0, Q, C, D = (d[k] for k in ("x0", "y0", "Q", "C", "D"))
    w = f"(({native_x})-({x0}))"
    vv = f"({native_y})"
    xexpr = f"(({Q})*({vv}+({y0}))+({D})*{w})/({w}^2)"
    yexpr = (
        f"(({Q})^3*({vv}+({y0}))+({Q})^2*(({D})*{w}+({C})*({w}^2))"
        f"-({D})^2*({w}^2))/(({Q})*({w}^3))"
    )
    return {"x": xexpr, "y": yexpr}


def covering_map_expressions(bundle):
    """Return exact map expressions for rank42.covering.v1 persistence."""
    return covering_map_expressions_from_native(bundle, "u", "v")
