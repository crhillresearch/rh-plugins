"""Exact operational models for Hill's two rational C2 rank-10 covers."""
from __future__ import annotations

import importlib.util
import json
from functools import lru_cache
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, sage_eval

HERE = Path(__file__).resolve().parent
R = PolynomialRing(QQ, "U")


@lru_cache(maxsize=2)
def data(index):
    return json.loads((HERE / "data" / f"cover-{index}" / "model.json").read_text())


def _poly(text):
    return R(str(text).replace("^", "**"))


def curve(index, value):
    try:
        u = QQ(value)
        model = data(index)["jacobian_model"]
        a4 = R([QQ(c) for c in model["a4_low_to_high"]])(u)
        a6 = R([QQ(c) for c in model["a6_low_to_high"]])(u)
        E = EllipticCurve(QQ, [0, 0, 0, a4, a6])
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(index, value, p):
    try:
        q = QQ(value)
        F = GF(int(p))
        u = F(q.numerator()) / F(q.denominator())
        model = data(index)["jacobian_model"]

        def evaluate(coefficients):
            result = F(0)
            for coefficient in reversed(coefficients):
                result = result * u + F(QQ(coefficient).numerator()) / F(QQ(coefficient).denominator())
            return result

        E = EllipticCurve(F, [0, 0, 0, evaluate(model["a4_low_to_high"]),
                              evaluate(model["a6_low_to_high"])])
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(index, value):
    E = curve(index, value)
    if E is None:
        return []
    u = QQ(value)
    points = []
    for row in data(index)["sections"]:
        try:
            x = _poly(row["x_numerator"])(u) / _poly(row["x_denominator"])(u)
            y = _poly(row["y_numerator"])(u) / _poly(row["y_denominator"])(u)
            points.append(E(x, y))
        except ZeroDivisionError:
            # A section may specialize to the point at infinity at an exceptional fiber.
            continue
    return points


def generic_section_metadata(index, value):
    if curve(index, value) is None:
        return []
    u = QQ(value)
    return [{"basis_label": row["label"], "source": f"rank-ledger:cover-{index}"}
            for row in data(index)["sections"]
            if _poly(row["x_denominator"])(u) and _poly(row["y_denominator"])(u)]


@lru_cache(maxsize=1)
def _replay_source_certificate():
    # Replay the exact correction-aware packet as published. It also checks the
    # separate genus-one rank-11 construction; this plugin only imports the two
    # individual Q(U) rank-10 claims returned below.
    spec = importlib.util.spec_from_file_location("hill_c2_rank10_source_verify", HERE / "verify.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verifier.main()
    return True


def validate_generic_rank_claim(index):
    _replay_source_certificate()
    return {
        "verified": True,
        "lower_bound": 10,
        "method": "Exact correction-aware Shioda Gram matrix replay over Q(U)",
        "certificate_version": "rank-ledger.c2-generic-rank10.v1",
        "details": {
            "cover": index,
            "gram_determinant": 11040,
            "inherited_block": "2*parent_rank9_gram",
            "new_section_orthogonal_residual_height": 3,
            "base_field": "Q(U)",
            "claim_boundary": "generic rank at least 10; exact generic rank undetermined",
        },
    }


def formula_family_data(index):
    """Expose the certified model to Rank Hunter's generic-family constructors."""
    model = data(index)

    def polynomial(coefficients):
        terms = []
        for exponent, coefficient in enumerate(coefficients):
            value = QQ(coefficient)
            if not value:
                continue
            term = f"({value})"
            if exponent:
                term += "*U" if exponent == 1 else f"*U**{exponent}"
            terms.append(term)
        return " + ".join(terms) or "0"

    sections = [
        {
            "label": row["label"],
            "x": f"({row['x_numerator']})/({row['x_denominator']})",
            "y": f"({row['y_numerator']})/({row['y_denominator']})",
            "source": f"rank-ledger:cover-{index}",
        }
        for row in model["sections"]
    ]
    return {
        "name": f"Hill C2 generic rank >=10 cover {index}",
        "parameter": "U",
        "a_invariants": [
            "0", "0", "0",
            polynomial(model["jacobian_model"]["a4_low_to_high"]),
            polynomial(model["jacobian_model"]["a6_low_to_high"]),
        ],
        "sections": sections,
        "generic_rank": 10,
        "verified_generic_rank_lower": 10,
        "generic_rank_claim_state": "generic_lower_bound_verified",
        "rank_lower_certificate": {
            "method": "exact_correction_aware_shioda_gram_replay",
            "source_generic_rank_lower_bound": 10,
            "cover": index,
            "gram_determinant": 11040,
            "source": "rank-ledger.c2-generic-rank10.v1",
        },
        "torsion_groups": ["C2"],
        "torsion_claim_machine_verified": True,
    }


def torsion_point(index, value):
    """Return the transformed visible 2-torsion point in short coordinates."""
    E = curve(index, value)
    if E is None:
        return None
    model = data(index)
    n = R([QQ(c) for c in model["quadratic_basechange"]["parameter_numerator"]])
    d = R([QQ(c) for c in model["quadratic_basechange"]["parameter_denominator"]])
    u = QQ(value)
    t = n(u) / d(u)
    source = json.loads((HERE / "data" / "source-family-u11_5.json").read_text())
    T = PolynomialRing(QQ, "t")
    tt = T.gen()
    a2 = sage_eval(str(source["a_invariants"][1]), locals={"t": tt})
    x = d(u) ** 4 * QQ(a2(t)) / 3
    return E(x, 0)


def validate_torsion_specialization(index, value=0):
    P = torsion_point(index, value)
    if P is None or not P or 2 * P:
        raise ValueError("transformed rational 2-torsion section failed")
    if list(P.curve().torsion_subgroup().invariants()) != [2]:
        raise ValueError("validation specialization does not have torsion exactly C2")
    return True
