"""Exact specialization interface for Hill's two rational rank-18 covers."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ


HERE = Path(__file__).resolve().parent
HASHES = {
    4339: "dcdd3403e0ed5b07c1a5cc00ffd068e7de0b272bf96d198cc73cea7eed134dc8",
    36773: "7b4246abbaf6bb846a0445518272f924ffc71f85dfb9aad7271feb21709baff5",
}
R = PolynomialRing(QQ, "U")


@lru_cache(maxsize=2)
def data(index):
    path = HERE / "data" / f"cover-{index}.json"
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != HASHES[index]:
        raise ValueError(f"cover {index} differs from the published proof packet")
    return json.loads(source)


def _coefficients(index, u, field):
    model = data(index)["jacobian_model"]
    return [field(0), field(0), field(0),
            field(R(model["a4_low_to_high"])(u)),
            field(R(model["a6_low_to_high"])(u))]


def curve(index, value):
    try:
        u = QQ(value)
        E = EllipticCurve(QQ, _coefficients(index, u, QQ))
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(index, value, p):
    try:
        q = QQ(value)
        F = GF(int(p))
        u = F(q.numerator()) / F(q.denominator())
        model = data(index)["jacobian_model"]

        def evaluate(values):
            result = F(0)
            for coefficient in reversed(values):
                result = result * u + F(coefficient)
            return result

        E = EllipticCurve(F, [0, 0, 0,
            evaluate(model["a4_low_to_high"]),
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
    for row in data(index)["neighbor_sections"]:
        def coordinate(axis):
            numerator = R(row[f"{axis}_numerator"].replace("^", "**"))(u)
            denominator = R(row[f"{axis}_denominator"].replace("^", "**"))(u)
            return numerator / denominator
        try:
            points.append(E(coordinate("x"), coordinate("y")))
        except ZeroDivisionError:
            # A rational section may meet the point at infinity on this fiber.
            continue
    return points


def generic_section_metadata(index, value):
    if curve(index, value) is None:
        return []
    u = QQ(value)
    return [{"basis_label": row["label"], "source": f"rank-ledger:cover-{index}"}
            for row in data(index)["neighbor_sections"]
            if R(row["x_denominator"].replace("^", "**"))(u)
            and R(row["y_denominator"].replace("^", "**"))(u)]


@lru_cache(maxsize=1)
def _verify_packet():
    spec = importlib.util.spec_from_file_location("hill_rank18_proof_replay", HERE / "verify.py")
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    verify.main()
    return True


def validate_generic_rank_claim(index):
    _verify_packet()
    return {
        "verified": True,
        "lower_bound": 18,
        "method": "Exact 18-section Shioda Gram and trivial-torsion proof replay",
        "certificate_version": "rank-ledger.generic-rank18-trivial-torsion.v1",
        "details": {
            "cover": index,
            "proof_packet_sha256": HASHES[index],
            "gram_determinant": 452984832,
            "extra_section_schur_complement": 3,
            "base_field": "Q(U)",
        },
    }
