"""Elkies 2026 first quadratic base change with 18 explicit sections.

The published cover is
    u^2 = 4225*t^2 + 38636*t + 289444.
Using the rational point at infinity u/t=65, parameterize it by
    t = (289444-r^2)/(130*r-38636),  u = 65*t+r.

P01..P17 are the published rank-17 sections pulled back along t(r).
P18 is the independently exact-verified recovered anti-invariant section.
"""
from __future__ import annotations

import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, sage_eval

HERE = Path(__file__).resolve().parent
R17_PATH = HERE.parent / "elkies_rank17_2026" / "family.json"
if not R17_PATH.is_file():
    raise RuntimeError(
        "Elkies Rank-18 First Cover requires the released Elkies Rank-17 K3 "
        f"family file at {R17_PATH}"
    )
R17 = json.loads(R17_PATH.read_text(encoding="utf-8"))

P18_X0 = [
    QQ("460616562639587423"),
    QQ("61544942274614409"),
    QQ("11682658506785981/2"),
    QQ("163024962070048"),
    QQ("1216010212300"),
]
P18_X1 = [
    QQ("855711822955990"),
    QQ("113254577959315/2"),
    QQ("2264387370700"),
    QQ("63585263040"),
]
P18_Y0 = [
    QQ("-441929137834774631820718940"),
    QQ("-88340690629574988024582045"),
    QQ("-22334275911806988301256955/2"),
    QQ("-1363110071200934708267785/2"),
    QQ("-26423100426660280883085"),
    QQ("-689209766348986114440"),
    QQ("-6652384198263573120"),
]
P18_Y1 = [
    QQ("-821427253437723585002350"),
    QQ("-218758612739524369513339/2"),
    QQ("-18589264629284251550843/2"),
    QQ("-371801596195754331919"),
    QQ("-6599542006586366552"),
    QQ("-63156938791842688"),
]

# Exact trace of the recovered P18 against Elkies's published P01..P17 basis.
# This is reconstruction provenance, not a coordinate printed in the paper.
P18_TRACE_VECTOR = (0, 0, 1, -1, 1, -1, 1, -1, 1, 0, 1, 1, 0, -1, -1, 0, 0)


def name():
    return "Elkies 2026 rank-18 first quadratic cover"


def generic_rank():
    # Operationally this is a verified generic lower bound: the 18th section is
    # exact and anti-invariant, and independence uses Elkies's base-change lemma.
    return 18


def _poly_eval(coeffs, x):
    out = x.parent()(0) if hasattr(x, "parent") else 0
    for c in reversed(coeffs):
        out = out * x + c
    return out


def _eval_r17(expr, t):
    return sage_eval(str(expr), locals={"t": t})


def _t_of_r(r):
    return (r.parent()(289444) - r * r) / (r.parent()(130) * r - r.parent()(38636))


def _u_of_r(r, t=None):
    if t is None:
        t = _t_of_r(r)
    return r.parent()(65) * t + r


def _ainvs_at_r(r):
    t = _t_of_r(r)
    return [_eval_r17(expr, t) for expr in R17["a_invariants"]]


def curve(r):
    try:
        rq = QQ(r)
        E = EllipticCurve(QQ, [QQ(a) for a in _ainvs_at_r(rq)])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r, p):
    try:
        F = GF(int(p))
        rr = F(int(r))
        E = EllipticCurve(F, [F(a) for a in _ainvs_at_r(rr)])
        if E.discriminant() == 0:
            return None
        return E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def generic_section_points(r):
    E = curve(r)
    if E is None:
        return []
    rq = QQ(r)
    t = _t_of_r(rq)
    u = _u_of_r(rq, t)
    out = []
    for idx, rec in enumerate(R17["sections"], 1):
        try:
            x = QQ(_eval_r17(rec["x"], t))
            y = QQ(_eval_r17(rec["y"], t))
            out.append(E(x, y))
        except Exception as exc:
            raise ValueError(f"pulled-back section P{idx:02d} failed at r={rq}: {exc}") from exc

    x18 = QQ(_poly_eval(P18_X0, t) + _poly_eval(P18_X1, t) * u)
    y18 = QQ(_poly_eval(P18_Y0, t) + _poly_eval(P18_Y1, t) * u)
    try:
        out.append(E(x18, y18))
    except Exception as exc:
        raise ValueError(f"recovered section P18 failed at r={rq}: {exc}") from exc
    return out


def validate_symbolically():
    R = PolynomialRing(QQ, "r")
    K = R.fraction_field()
    r = K(R.gen())
    t = _t_of_r(r)
    u = _u_of_r(r, t)
    q = 4225 * t**2 + 38636 * t + 289444
    if u**2 != q:
        raise ValueError("rank-18 conic parameterization identity failed")

    ainvs = [K(_eval_r17(expr, t)) for expr in R17["a_invariants"]]
    E = EllipticCurve(K, ainvs)
    points = []
    for idx, rec in enumerate(R17["sections"], 1):
        x = K(_eval_r17(rec["x"], t))
        y = K(_eval_r17(rec["y"], t))
        try:
            points.append(E(x, y))
        except Exception as exc:
            raise ValueError(f"pulled-back generic section P{idx:02d} is off curve") from exc

    x18 = K(_poly_eval(P18_X0, t) + _poly_eval(P18_X1, t) * u)
    y18 = K(_poly_eval(P18_Y0, t) + _poly_eval(P18_Y1, t) * u)
    try:
        points.append(E(x18, y18))
    except Exception as exc:
        raise ValueError("recovered generic P18 is off the rank-18 cover") from exc

    return {
        "name": name(),
        "generic_rank_declared": generic_rank(),
        "base_field": "Q(r)",
        "published_cover": "u^2=4225*t^2+38636*t+289444",
        "parameterization_verified": True,
        "sections_verified_on_curve": len(points),
        "recovered_p18_verified": True,
        "discriminant": str(E.discriminant()),
    }


def _verify_quadratic_cover_section():
    """Verify recovered P18 before rationally parameterizing the quadratic cover."""
    R = PolynomialRing(QQ, "t")
    t = R.gen()
    K = R.fraction_field()
    q = K(4225 * t**2 + 38636 * t + 289444)

    U = PolynomialRing(K, "z")
    z = U.gen()
    L = K.extension(z**2 - q, names=("u",))
    u = L.gen()

    ainvs = [L(K(_eval_r17(expr, t))) for expr in R17["a_invariants"]]
    E = EllipticCurve(L, ainvs)

    basis = []
    for idx, rec in enumerate(R17["sections"], 1):
        x = L(K(_eval_r17(rec["x"], t)))
        y = L(K(_eval_r17(rec["y"], t)))
        try:
            basis.append(E(x, y))
        except Exception as exc:
            raise ValueError(
                f"published section P{idx:02d} failed on the quadratic cover"
            ) from exc

    x0 = K(_poly_eval(P18_X0, t))
    x1 = K(_poly_eval(P18_X1, t))
    y0 = K(_poly_eval(P18_Y0, t))
    y1 = K(_poly_eval(P18_Y1, t))
    try:
        p18 = E(L(x0) + L(x1) * u, L(y0) + L(y1) * u)
        conjugate = E(L(x0) - L(x1) * u, L(y0) - L(y1) * u)
    except Exception as exc:
        raise ValueError("recovered P18 failed exact quadratic-cover identity") from exc

    if p18 == conjugate:
        raise ValueError("recovered P18 is Galois invariant")

    trace = E(0)
    for coefficient, point in zip(P18_TRACE_VECTOR, basis):
        trace += int(coefficient) * point
    if p18 + conjugate != trace:
        raise ValueError("recovered P18 trace does not match the rank-17 basis relation")

    return {
        "published_cover": "u^2=4225*t^2+38636*t+289444",
        "quadratic_cover_field": "Q(t,u)",
        "published_basis_size": len(basis),
        "p18_exact_on_cover": True,
        "galois_anti_invariant_nonzero": True,
        "trace_identity_verified": True,
        "trace_basis_vector": list(P18_TRACE_VECTOR),
    }


def validate_generic_rank_claim():
    """Validate the operational generic lower bound required by Rank Hunter core."""
    symbolic = validate_symbolically()
    if int(symbolic.get("sections_verified_on_curve", 0)) != 18:
        raise ValueError("generic rank claim requires all 18 sections on the cover")
    if not symbolic.get("parameterization_verified") or not symbolic.get("recovered_p18_verified"):
        raise ValueError("generic rank claim requires exact cover and P18 verification")

    quadratic = _verify_quadratic_cover_section()

    return {
        "verified": True,
        "lower_bound": 18,
        "method": "Elkies equation (11) quadratic base change + 17 published independent sections + exact non-Galois-invariant recovered P18 with verified trace relation",
        "certificate_version": "rank-hunter.elkies-rank18-first-cover-generic-lower.v2",
        "details": {
            "arxiv": "2608.25406v1",
            "published_cover": symbolic["published_cover"],
            "base_field": symbolic["base_field"],
            "sections_verified_on_curve": symbolic["sections_verified_on_curve"],
            "parameterization_verified": True,
            "recovered_p18_verified": True,
            **quadratic,
        },
    }
