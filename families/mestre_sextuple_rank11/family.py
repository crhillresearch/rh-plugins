"""Mestre/Fermigier rank-11 sextuple family used by recent ICARM controls.

This module implements the fixed integer sextuple

    a = [348, -600, -216, 492, 876, -900]

with parameter ``t`` through Mestre's polynomial construction

    p6(z) = prod_i (z-a_i),
    q_t(x) = p6(x-t) p6(x+t).

For this sextuple the square-completion remainder drops from the generic
possible degree 5 to degree 4.  With the explicit degree-six polynomial G_t
used below, the exact identity is

    G_t(x)^2 - q_t(x) = (539136*t)^2 r_t(x),

where ``r_t`` is the normalized quartic returned by
``quartic_search_coefficients``.  Hence, for t != 0, the genus-one curve

    C_t : y^2 = r_t(x)

contains the twelve exact rational base points

    x = a_i + t  and  x = a_i - t,
    y = G_t(x)/(539136*t).

One base point is chosen as the elliptic origin and the other eleven are
exposed as the family section set.  Rank Hunter 0.9.2 independently certifies
those eleven sections at a good rational specialization before accepting the
operational generic lower bound 11; a section list or numerical height screen
alone is not treated as a proof.

The normalized quartic depends only on t^2, so C_t = C_-t exactly as native
quartic equations.  Rank Hunter therefore canonicalizes the parameter orbit
`t ~ -t` during candidate generation and Mestre batch search.

Positive-control provenance
---------------------------
ICARM leaderboard entries #187, #190, and #211 document this same sextuple at
respectively t=842/9, 1069/4, and 2326/23.  #187 and #190 have certified lower
bound >=16; #211 has certified lower bound >=11.  Those public specialization
results are external controls, not proofs of every claim made by this module.

Mathematical reference
----------------------
J.-F. Mestre, "Courbes elliptiques de rang >= 11 sur Q(t)",
C. R. Acad. Sci. Paris Ser. I Math. 313 (1991), 139-142.

The quartic-to-Weierstrass map is the same exact rational-point construction
already used by Rank Hunter's Kihara module: translate a rational quartic point
to x=0 and use the standard generalized Weierstrass transformation.
"""

from __future__ import annotations

from sage.all import QQ, GF, EllipticCurve, PolynomialRing


generic_rank = 11
historical_generic_rank_lower = 11
parameter_symmetry = "sign"

SEXTUPLE = (348, -600, -216, 492, 876, -900)
NORMALIZATION = 539136

FAMILY_LAB_METADATA = {
    "sections_declared": 11,
    "status": "reconstructed Mestre/Fermigier family",
    "point_search_adapter": "native quartic + exact PGL2 charts + staged ratpoints + exact subgroup certificate",
    "provenance": (
        "Mestre polynomial rank-11 construction; fixed sextuple and successful "
        "specializations documented by ICARM curves #187, #190, and #211."
    ),
    "notes": (
        "The module supplies twelve exact quartic base fibres and eleven non-origin "
        "section points. The native quartic has exact t <-> -t symmetry, so search "
        "pools use one canonical parameter orbit representative. Native and exact PGL2 chart search are available; independence/certification remains separate."
    ),
}


def name():
    return "Mestre/Fermigier sextuple, generic rank >=11"


def canonical_parameter(t):
    """Return the canonical representative of the exact t <-> -t orbit.

    The native quartic coefficients are even in t, so +/-t are the same
    native genus-one search target.  The positive rational representative is
    used for candidate generation and batch search deduplication.
    """
    tq = QQ(t)
    return -tq if tq < 0 else tq


def parameter_orbit_key(t):
    """Stable exact key for the native-quartic parameter orbit."""
    return str(canonical_parameter(t))


def _quartic_coefficients(t):
    """Return normalized a0,...,a4 for r_t(x) over the parent ring of t."""
    t2 = t * t
    t4 = t2 * t2
    t6 = t4 * t2
    return [
        t6 - 927200 * t4 + 109659379968 * t2 + 97964663431680000,
        -101347200 * (t2 - 234720),
        -2 * (t4 - 739200 * t2 + 596846316672),
        -60808320 + 0 * t,
        t2 + 3391200,
    ]


def _g_coefficients(t):
    """Return g0,...,g6 for the exact square-completion polynomial G_t."""
    t2 = t * t
    t4 = t2 * t2
    t6 = t4 * t2
    return [
        -t6 + 1173600 * t4 - 471501326592 * t2 - 17494275594240000,
        121616640 * (t2 - 195600),
        3 * (t4 + 108722504448),
        40538880 + 0 * t,
        -3 * (t2 + 391200),
        0 * t,
        1 + 0 * t,
    ]


def _poly_from_coefficients(R, coeffs):
    x = R.gen()
    return sum((coeffs[i] * x**i for i in range(len(coeffs))), R.zero())


def _quartic_polynomial(t, R=None):
    if R is None:
        R = PolynomialRing(t.parent(), "x")
    return _poly_from_coefficients(R, _quartic_coefficients(t))


def _g_polynomial(t, R=None):
    if R is None:
        R = PolynomialRing(t.parent(), "x")
    return _poly_from_coefficients(R, _g_coefficients(t))


def _base_x_values(t):
    """The twelve roots of p6(x-t)p6(x+t), plus-shift block first."""
    return [t + a for a in SEXTUPLE] + [a - t for a in SEXTUPLE]


def _native_data(t):
    """Return exact native quartic data over QQ for one nonzero specialization."""
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Mestre sextuple construction degenerates at t=0")

    R = PolynomialRing(QQ, "x")
    x = R.gen()
    quartic = _quartic_polynomial(tq, R)
    G = _g_polynomial(tq, R)
    scale = QQ(NORMALIZATION) * tq

    roots = [QQ(xx) for xx in _base_x_values(tq)]
    if len(set(roots)) != 12:
        raise ArithmeticError("specialization has colliding Mestre base fibres")

    points = []
    for xx in roots:
        yy = QQ(G(xx) / scale)
        if yy * yy != quartic(xx):
            raise ArithmeticError("Mestre square-completion identity failed at a base fibre")
        points.append((xx, yy))

    return R, x, G, quartic, roots, points


def _quartic_invariants_from_coefficients(coeffs):
    """Classical invariants I,J of a*x^4+b*x^3+c*x^2+d*x+e."""
    e, d, c, b, a = coeffs
    I = 12 * a * e - 3 * b * d + c**2
    J = 72 * a * c * e + 9 * b * c * d - 27 * a * d**2 - 27 * b**2 * e - 2 * c**3
    return I, J


def _quartic_invariants(quartic):
    return _quartic_invariants_from_coefficients([quartic[i] for i in range(5)])


def _choose_origin(points):
    """Choose the first base point with nonzero y so the map is nondegenerate."""
    for index, (_, yy) in enumerate(points):
        if yy != 0:
            return index
    raise ArithmeticError("all Mestre base points have y=0; no usable quartic origin")


def _map_quartic_point(E, data, xq, yq):
    """Map an affine point on the normalized quartic to E(Q) exactly."""
    x0, y0, Q = data["x0"], data["y0"], data["Q"]
    C, D = data["C"], data["D"]
    u = QQ(xq) - x0
    v = QQ(yq)

    if u == 0:
        if v == y0:
            return E(0)
        if v == -y0 and data.get("involution_translation") is not None:
            return data["involution_translation"]
        raise ArithmeticError("point above the chosen quartic origin needs the exceptional map")

    X = (Q * (v + y0) + D * u) / u**2
    Y = (
        Q**3 * (v + y0)
        + Q**2 * (D * u + C * u**2)
        - D**2 * u**2
    ) / (Q * u**3)
    return E(QQ(X), QQ(Y))


def _rational_model(t):
    """Return (E, map_data, native_data) over QQ for a good specialization."""
    tq = QQ(t)
    R, x, G, quartic, roots, points = _native_data(tq)

    origin_index = _choose_origin(points)
    x0, y0 = points[origin_index]

    s = R.gen()
    rt = quartic(s + x0)
    A, B, C, D = (QQ(rt[4]), QQ(rt[3]), QQ(rt[2]), QQ(rt[1]))
    if QQ(rt[0]) != y0**2:
        raise ArithmeticError("translated Mestre quartic lost the chosen rational origin")

    Q = 2 * y0
    a1 = D / y0
    a2 = C - (D / Q) ** 2
    a3 = B * Q
    a4 = -A * Q**2
    a6 = a2 * a4
    E = EllipticCurve(QQ, [a1, a2, a3, a4, a6])
    if E.discriminant() == 0:
        raise ArithmeticError("singular Mestre sextuple specialization")

    data = {
        "x0": x0,
        "y0": y0,
        "Q": Q,
        "A": A,
        "B": B,
        "C": C,
        "D": D,
        "origin_index": int(origin_index),
        "involution_translation": None,
    }

    # The opposite sign above x0 is the exceptional point of this affine map.
    # Determine its elliptic image exactly from any other base fibre.  On a
    # genus-one quartic the hyperelliptic involution has the form P -> T-P.
    for index, (xx, yy) in enumerate(points):
        if index == origin_index:
            continue
        P = _map_quartic_point(E, data, xx, yy)
        Pi = _map_quartic_point(E, data, xx, -yy)
        data["involution_translation"] = P + Pi
        break
    if data["involution_translation"] is None:
        raise ArithmeticError("could not determine quartic involution translation")

    return E, data, (R, x, G, quartic, roots, points)


def curve(t):
    """Return a rational Weierstrass model, or None for a bad specialization."""
    try:
        E, _, _ = _rational_model(t)
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def screen_curve(t):
    """Cheap QQ Jacobian model used only for rank screening."""
    try:
        tq = QQ(t)
        if tq == 0:
            return None
        coeffs = _quartic_coefficients(tq)
        I, J = _quartic_invariants_from_coefficients(coeffs)
        E = EllipticCurve(QQ, [0, 0, 0, -27 * I, -27 * J])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def screen_model_name():
    return "binary_quartic_jacobian"


def curve_mod_p(r0, p0):
    """Return the normalized quartic Jacobian over F_p for Nagao scoring.

    ``r0`` is already the residue of the rational specialization a/b modulo p
    as supplied by rank42.nagao.  The t=0 residue is skipped because the twelve
    Mestre base fibres coalesce in the original square-completion construction.
    Characteristics 2 and 3 are skipped, matching Rank Hunter's Kihara path.
    """
    try:
        p = int(p0)
        if p in (2, 3):
            return None
        K = GF(p)
        t = K(int(r0))
        if t == 0:
            return None
        coeffs = _quartic_coefficients(t)
        I, J = _quartic_invariants_from_coefficients(coeffs)
        E = EllipticCurve(K, [0, 0, 0, -27 * I, -27 * J])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def native_quartic_known_points(t):
    """Return the twelve exact Mestre base points on y^2=r_t(x)."""
    return list(_native_data(QQ(t))[5])


def native_quartic_known_x(t):
    return [P[0] for P in native_quartic_known_points(t)]


def quartic_search_coefficients(t):
    """Return exact normalized a0,...,a4 for the native quartic."""
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Mestre sextuple construction degenerates at t=0")
    return [QQ(c) for c in _quartic_coefficients(tq)]


def _generic_sections_from_model(E, data, native_data):
    """Map the eleven non-origin Mestre base points to E(Q)."""
    points = native_data[5]
    origin_index = int(data["origin_index"])
    out = []
    for index, (xx, yy) in enumerate(points):
        if index == origin_index:
            continue
        P = _map_quartic_point(E, data, xx, yy)
        if P.is_zero():
            raise ArithmeticError("a non-origin Mestre base point mapped to the identity")
        out.append(P)
    if len(out) != 11:
        raise ArithmeticError("Mestre construction did not produce eleven non-origin sections")
    return out


def generic_section_points(t):
    """Specialize the eleven non-origin Mestre base sections."""
    E, data, native_data = _rational_model(t)
    return _generic_sections_from_model(E, data, native_data)


def direct_search_bundle(t):
    """Materialize the full exact model only after a cheap quartic scout hits."""
    tq = QQ(t)
    E, data, native_data = _rational_model(tq)
    basis = _generic_sections_from_model(E, data, native_data)
    quartic = native_data[3]
    return {
        "curve": E,
        "basis": basis,
        "map_data": data,
        "quartic_coefficients": [QQ(quartic[i]) for i in range(5)],
        "native_points": list(native_data[5]),
    }


def map_native_quartic_point(bundle, x, y):
    """Map an exact affine point on the normalized quartic to bundle['curve']."""
    return _map_quartic_point(
        bundle["curve"], bundle["map_data"], QQ(str(x)), QQ(str(y))
    )


def native_quartic_involution_translation(bundle, t):
    """Return exact T such that the quartic involution maps P to T-P."""
    T = bundle["map_data"].get("involution_translation")
    if T is None:
        raise ArithmeticError("quartic involution translation was not initialized")

    for xq, yq in native_quartic_known_points(t):
        P = map_native_quartic_point(bundle, xq, yq)
        Pi = map_native_quartic_point(bundle, xq, -yq)
        if P + Pi != T:
            raise ArithmeticError("Mestre quartic involution failed exact P -> T-P check")
    return T


def native_quartic_involution_controls(bundle, t):
    """Return exact positive-control pairs for every known base fibre."""
    T = native_quartic_involution_translation(bundle, t)
    out = []
    for index, (xq, yq) in enumerate(native_quartic_known_points(t), 1):
        P = map_native_quartic_point(bundle, xq, yq)
        Pi = map_native_quartic_point(bundle, xq, -yq)
        if Pi != T - P:
            raise ArithmeticError(f"Mestre involution relation failed on base fibre {index}")
        out.append(
            {
                "index": index,
                "native_point": (QQ(xq), QQ(yq)),
                "published_image": P,
                "opposite_image": Pi,
                "translation": T,
            }
        )
    return out


def covering_map_expressions_from_native(bundle, native_x="u", native_y="v"):
    """Compose the native quartic map with exact covering input expressions."""
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
    return covering_map_expressions_from_native(bundle, "u", "v")


def construction_check(t=QQ(1069) / QQ(4)):
    """Exact specialization-level consistency check; no height computation."""
    tq = QQ(t)
    bundle = direct_search_bundle(tq)
    E = bundle["curve"]
    basis = bundle["basis"]
    native = native_quartic_known_points(tq)
    coeffs = quartic_search_coefficients(tq)

    for xx, yy in native:
        rhs = sum((coeffs[i] * xx**i for i in range(5)), QQ(0))
        if yy**2 != rhs:
            raise ArithmeticError("known Mestre point failed the normalized quartic equation")

    screen = screen_curve(tq)
    if screen is None or screen.j_invariant() != E.j_invariant():
        raise ArithmeticError("quartic Jacobian and rational-origin model disagree on j-invariant")

    return {
        "family": name(),
        "parameter": str(tq),
        "base_fibres": len(native),
        "sections": len(basis),
        "distinct_nonzero": len(
            {(QQ(P[0]), QQ(P[1])) for P in basis if not P.is_zero()}
        ),
        "quartic_coefficients": [str(c) for c in coeffs],
        "j_invariant": str(E.j_invariant()),
        "t_sign_quartic_symmetry": coeffs == quartic_search_coefficients(-tq),
    }


def validate_symbolically():
    """Verify the square-completion identity exactly over Q(t).

    This proves the twelve displayed base fibres lie on the normalized quartic
    over Q(t).  It deliberately does not claim Mordell-Weil independence.
    """
    T = PolynomialRing(QQ, "t")
    tpoly = T.gen()
    K = T.fraction_field()
    t = K(tpoly)
    R = PolynomialRing(K, "x")
    x = R.gen()

    p6_minus = R.one()
    p6_plus = R.one()
    for a in SEXTUPLE:
        p6_minus *= x - t - a
        p6_plus *= x + t - a
    q = p6_minus * p6_plus

    G = _g_polynomial(t, R)
    quartic = _quartic_polynomial(t, R)
    scale = K(NORMALIZATION) * t
    if G * G - q != scale**2 * quartic:
        raise ArithmeticError("symbolic Mestre square-completion identity failed")

    for xx in _base_x_values(t):
        yy = G(xx) / scale
        if yy**2 != quartic(xx):
            raise ArithmeticError("symbolic Mestre base point failed the quartic equation")

    return {
        "family": name(),
        "identity_verified": True,
        "base_fibres_verified": 12,
        "sections_verified_on_curve": 11,
        "normalization": str(NORMALIZATION),
        "claim_scope": "exact Q(t) quartic identity and on-curve section verification only",
    }



def validate_generic_rank_claim():
    """Exact-certify the eleven reconstructed Mestre sections at a good fiber.

    Exact independence at one good specialization proves generic independence:
    any integral relation among the sections over Q(t) would specialize to the
    same relation at that fiber.
    """
    from rank42.exact_lb import run_exact_certificate

    control_parameter = "1"
    E = curve(control_parameter)
    if E is None:
        raise RuntimeError(
            f"Mestre generic-rank control t={control_parameter} is singular or undefined"
        )
    points = generic_section_points(control_parameter)
    if len(points) != 11 or any(P.is_zero() for P in points):
        raise RuntimeError(
            f"Mestre control produced {len(points)} sections; expected 11 nonzero points"
        )

    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=240,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    verified = bool(exact.get("independent") is True and lower >= 11)
    return {
        "verified": verified,
        "lower_bound": lower,
        "method": (
            "11 exact Mestre/Fermigier sections + Rank Hunter exact "
            "independence certificate at t=1"
        ),
        "certificate_version": "mestre-sextuple-rank11-generic-lower-v1.5.2",
        "details": {
            "control_parameter": control_parameter,
            "section_count": len(points),
            "specialization_certificate": exact,
            "generic_argument": (
                "any integral relation among the eleven explicit generic sections "
                "would specialize at this good fiber; exact independence there "
                "therefore proves generic independence"
            ),
            "published_claim": "Mestre 1991: generic rank at least 11 over Q(t)",
        },
    }
