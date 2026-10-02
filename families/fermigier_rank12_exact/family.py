"""Exact Fermigier--Mestre one-parameter family of arithmetic generic rank 12.

The canonical Rank Hunter parameter is ``u``.  Fermigier's literal symmetric
shift is ``s = 2*u``.  The fixed roots are

    (0, 55, 314, 378, 1007, 1036).

For the literal shift ``s``, square-completion of
``p6(x-s)*p6(x+s)`` gives a normalized genus-one quartic

    C_u : y^2 = r_u(x),

after division by ``(50616*s)^2 = (101232*u)^2``.  The quartic has twelve
root-derived rational points plus Fermigier's material thirteenth point.  A
rational quartic point is chosen as origin, so the remaining twelve points
become exact specialized sections on a deterministic Weierstrass model.

The frozen reconstruction artifact ``elliptic_fermigier_generic_rank_exact.json``
reports unconditionally that the arithmetic generic Mordell--Weil rank over
Q(u) is exactly 12.  The public RELEASE validator does not re-prove that
upper bound: it independently verifies the operational generic lower bound 12
by exact independence of the twelve explicit sections after specialization.
Rank Hunter also re-certifies specialized independence before promoting any
specialization lower bound.

The normalized quartic and canonical Weierstrass coefficients are even in u,
so u and -u represent the same native search target.
"""

from __future__ import annotations

from pathlib import Path

from sage.all import QQ, GF, EllipticCurve, PolynomialRing


generic_rank = 12
historical_generic_rank_lower = 12
parameter_symmetry = "sign"
source_path = Path(__file__)

ROOTS = (0, 55, 314, 378, 1007, 1036)
NORMALIZATION = 101232

FAMILY_LAB_METADATA = {
    "sections_declared": 12,
    "status": "generic lower bound 12 verified operationally; frozen reconstruction artifact reports arithmetic generic rank exactly 12 over Q(u)",
    "point_search_adapter": "native quartic + exact PGL2 charts + staged ratpoints + exact subgroup certificate",
    "provenance": (
        "Fermigier--Mestre fixed-root K3; exact generic-rank theorem replayed by "
        "elliptic-curves/cas/verify_fermigier_generic_rank_exact.py."
    ),
    "notes": (
        "Thirteen exact quartic sections are materialized; one is used as origin and "
        "the remaining twelve form the generic subgroup. Every specialization rank "
        "promotion still requires an exact independence certificate."
    ),
}



def name():
    return "Fermigier--Mestre K3, generic rank >= 12"


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


def _literal_shift(t):
    return 2 * t


def _quartic_coefficients(t):
    """Return normalized a0,...,a4 for y^2=r_u(x), low to high."""
    s = _literal_shift(t)
    s2 = s * s
    s4 = s2 * s2
    s6 = s4 * s2
    return [
        s6 - 879500 * s4 + 102302344648 * s2 + 18103855887324900,
        30 * (62 * s4 - 21690305 * s2 - 8594794400346),
        -(2 * s4 - 1718550 * s2 - 1195214262641),
        -30 * (62 * s2 + 68377393),
        s2 + 1149050,
    ]


def _g_coefficients(t):
    """Return low-to-high coefficients of the unscaled square approximant g(X,s)."""
    s = _literal_shift(t)
    s2 = s * s
    s4 = s2 * s2
    s6 = s4 * s2
    return [
        -s6 + 1165925 * s4 - 128370083212 * s2,
        -2790 * s4 + 1034713080 * s2 - 6810411651120,
        3 * s4 - 3892050 * s2 + 176868664084,
        5580 * s2 - 1106081640,
        2726125 - 3 * s2,
        -2790 + 0 * t,
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
    """The twelve root-derived abscissas, in the certificate's primitive order."""
    s = _literal_shift(t)
    return [QQ(root) + sign * s for root in ROOTS for sign in (-1, 1)]


def _extra_point(t, quartic):
    """Fermigier's thirteenth normalized quartic point, with exact chosen sign."""
    s = _literal_shift(t)
    xx = QQ(1256) / QQ(5) - QQ(17) * s / QQ(35)
    yy = (
        936 * s**3
        - 254422 * s**2
        - 283436139 * s
        + 34925066050
    ) / QQ(1225)
    if yy * yy != quartic(xx):
        raise ArithmeticError("Fermigier thirteenth point failed the normalized quartic equation")
    return QQ(xx), QQ(yy)


def _native_data(t):
    """Return exact normalized quartic data over QQ for one nonzero specialization."""
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Fermigier normalized point construction degenerates at u=0")

    R = PolynomialRing(QQ, "x")
    x = R.gen()
    quartic = _quartic_polynomial(tq, R)
    G = _g_polynomial(tq, R)
    scale = QQ(NORMALIZATION) * tq

    roots = [QQ(xx) for xx in _base_x_values(tq)]
    if len(set(roots)) != 12:
        raise ArithmeticError("specialization has colliding Fermigier root fibres")

    points = []
    for xx in roots:
        yy = QQ(G(xx) / scale)
        if yy * yy != quartic(xx):
            raise ArithmeticError("Fermigier square-completion identity failed at a root fibre")
        points.append((xx, yy))

    points.append(_extra_point(tq, quartic))
    if len(set(xx for xx, _ in points)) != 13:
        raise ArithmeticError("Fermigier thirteenth section collided with a root-derived fibre")

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
    raise ArithmeticError("all Fermigier known points have y=0; no usable quartic origin")


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
        raise ArithmeticError("translated Fermigier quartic lost the chosen rational origin")

    Q = 2 * y0
    a1 = D / y0
    a2 = C - (D / Q) ** 2
    a3 = B * Q
    a4 = -A * Q**2
    a6 = a2 * a4
    E = EllipticCurve(QQ, [a1, a2, a3, a4, a6])
    if E.discriminant() == 0:
        raise ArithmeticError("singular Fermigier specialization")

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
    as supplied by rank42.nagao.  The u=0 residue is skipped because the
    normalized visible-section construction uses division by the literal shift.
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
    """Return the thirteen exact Fermigier points on the normalized quartic."""
    return list(_native_data(QQ(t))[5])


def native_quartic_known_x(t):
    return [P[0] for P in native_quartic_known_points(t)]


def quartic_search_coefficients(t):
    """Return exact normalized a0,...,a4 for the native quartic."""
    tq = QQ(t)
    if tq == 0:
        raise ZeroDivisionError("Fermigier normalized construction degenerates at u=0")
    return [QQ(c) for c in _quartic_coefficients(tq)]


def _generic_sections_from_model(E, data, native_data):
    """Map the twelve non-origin Fermigier points to E(Q)."""
    points = native_data[5]
    origin_index = int(data["origin_index"])
    out = []
    for index, (xx, yy) in enumerate(points):
        if index == origin_index:
            continue
        P = _map_quartic_point(E, data, xx, yy)
        if P.is_zero():
            raise ArithmeticError("a non-origin Fermigier known point mapped to the identity")
        out.append(P)
    if len(out) != 12:
        raise ArithmeticError("Fermigier construction did not produce twelve non-origin sections")
    return out


def generic_section_points(t):
    """Specialize the twelve non-origin Fermigier sections."""
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
            raise ArithmeticError("Fermigier quartic involution failed exact P -> T-P check")
    return T


def native_quartic_involution_controls(bundle, t):
    """Return exact positive-control pairs for every known base fibre."""
    T = native_quartic_involution_translation(bundle, t)
    out = []
    for index, (xq, yq) in enumerate(native_quartic_known_points(t), 1):
        P = map_native_quartic_point(bundle, xq, yq)
        Pi = map_native_quartic_point(bundle, xq, -yq)
        if Pi != T - P:
            raise ArithmeticError(f"Fermigier involution relation failed on known fibre {index}")
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


def construction_check(t=QQ(19754) / QQ(39)):
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
            raise ArithmeticError("known Fermigier point failed the normalized quartic equation")

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
    """Verify the Fermigier square-completion and all thirteen points over Q(u).

    This is an exact construction regression.  The frozen reconstruction
    theorem is separate provenance for the reported arithmetic upper bound.
    """
    U = PolynomialRing(QQ, "u")
    upoly = U.gen()
    K = U.fraction_field()
    u = K(upoly)
    s = 2 * u
    R = PolynomialRing(K, "x")
    x = R.gen()

    p6_minus = R.one()
    p6_plus = R.one()
    for root in ROOTS:
        p6_minus *= x - s - root
        p6_plus *= x + s - root
    q = p6_minus * p6_plus

    G = _g_polynomial(u, R)
    quartic = _quartic_polynomial(u, R)
    scale = K(NORMALIZATION) * u
    if G * G - q != scale**2 * quartic:
        raise ArithmeticError("symbolic Fermigier square-completion identity failed")

    for xx in _base_x_values(u):
        yy = G(xx) / scale
        if yy**2 != quartic(xx):
            raise ArithmeticError("symbolic Fermigier root-derived point failed the quartic equation")

    extra_x = K(1256) / K(5) - K(17) * s / K(35)
    extra_y = (
        936 * s**3 - 254422 * s**2 - 283436139 * s + 34925066050
    ) / K(1225)
    if extra_y**2 != quartic(extra_x):
        raise ArithmeticError("symbolic Fermigier thirteenth point failed the quartic equation")

    return {
        "family": name(),
        "identity_verified": True,
        "quartic_points_verified": 13,
        "sections_after_origin": 12,
        "normalization": str(NORMALIZATION),
        "parameter_bridge": "literal shift s=2*u",
        "claim_scope": "exact Q(u) construction regression; generic lower-bound independence is certified separately",
    }


def validate_generic_rank_claim():
    """Verify the twelve explicit sections are generically independent.

    Exact independence at one good specialization proves generic independence:
    any integral relation among the sections over Q(u) would specialize to the
    same relation at that fiber.
    """
    from rank42.exact_lb import run_exact_certificate

    control_parameter = "7/3"
    E = curve(control_parameter)
    if E is None:
        raise RuntimeError(
            f"Fermigier-Mestre control u={control_parameter} is singular or undefined"
        )
    points = generic_section_points(control_parameter)
    if len(points) != 12:
        raise RuntimeError(
            f"Fermigier-Mestre control produced {len(points)} sections, expected 12"
        )

    exact = run_exact_certificate(
        E.a_invariants(),
        [[P[0], P[1]] for P in points],
        timeout=180,
    )
    lower = int(exact.get("rank_lower_bound") or 0)
    verified = bool(exact.get("independent") is True and lower >= 12)
    return {
        "verified": verified,
        "lower_bound": lower,
        "method": "12 exact Fermigier-Mestre sections + exact specialized independence certificate",
        "certificate_version": "fermigier-mestre-k3-generic-lower-v1.1.0",
        "details": {
            "control_parameter": control_parameter,
            "literal_shift": str(2 * QQ(control_parameter)),
            "section_count": len(points),
            "specialization_certificate": exact,
            "generic_argument": (
                "any integral relation among the twelve explicit generic sections "
                "would specialize at this good fiber; exact specialized independence "
                "therefore verifies generic independence"
            ),
            "upper_bound_provenance": (
                "frozen reconstruction artifact reports arithmetic generic rank "
                "exactly 12; this release certificate proves only the lower bound"
            ),
        },
    }
