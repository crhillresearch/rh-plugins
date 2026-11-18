"""C. R. Hill's rank-19 K3 family, indexed by points on a genus-one base.

The integer input n means n times the recorded infinite-order auxiliary point.
It is an index for rational specializations, not a rational coordinate on the
parameter base. The generic rank claim is over Q(E_aux), not Q(t).
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from math import gcd
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, ZZ, matrix


_DATA = json.loads(Path(__file__).with_name("construction.json").read_text())
_PROOF = _DATA["proof"]
_PAIR = _PROOF["pair"]
_R = PolynomialRing(QQ, "z")
_N = _R(_PAIR["parent_numerator"])
_D = _R(_PAIR["parent_denominator"])
_W = _R(_PAIR["first_root_numerator"])
_F = _R(_PAIR["quartic"])
_A4 = _R(_DATA["parent_jacobian_model"]["a4_low_to_high"])
_A6 = _R(_DATA["parent_jacobian_model"]["a6_low_to_high"])

generic_rank = 19
parameter_base_genus = 1
# The map from the auxiliary elliptic curve to the K3 parameter is invariant
# under Q -> P-Q.  On integer multiples this is n -> 1-n, so keep n >= 1 as
# the unique representative of each rational fiber.
parameter_symmetry = "canonical"


def name():
    return "Hill Rank-19 K3"


def candidate_seed_parameters():
    """Include the reproducible n=1 construction fiber in each hunt."""
    return (1,)


def canonical_parameter(value):
    """Return the canonical integer multiple for the fiber indexed by value."""
    q = Fraction(value)
    if q.denominator == 1 and q.numerator < 1:
        q = 1 - q
    return q.numerator, q.denominator


def parent_parameter(index):
    """Map nP on the auxiliary elliptic curve to the original family t."""
    n = QQ(index)
    if not n.is_integer() or not n:
        raise ValueError("parameter must be a nonzero integer auxiliary-point multiple")
    E = EllipticCurve(QQ, _PAIR["auxiliary_a_invariants"])
    P = E(*map(QQ, _PAIR["auxiliary_point"]))
    T = int(n) * P
    if not T:
        raise ValueError("auxiliary multiple is the point at infinity")
    X, Y = T.xy()
    e = _F[0].sqrt()
    a, b, d = _F[4], _F[3], _F[1]
    denominator = X * X - 4 * e * e * a
    if not denominator:
        raise ValueError("auxiliary point maps to the quartic origin")
    z = (2 * e * Y + X * d + 2 * e * e * b) / denominator
    if not _D(z):
        raise ValueError("auxiliary point maps to parent infinity")
    w = (X * z * z - d * z - 2 * e * e) / (2 * e)
    if w * w != _F(z):
        raise ArithmeticError("auxiliary point failed the quartic identity")
    t = _N(z) / _D(z)
    roots = (_W(z) / _D(z), w / _D(z))
    for coefficients, root in zip(_DATA["cover_coefficients"], roots):
        if _R(coefficients)(t) != root * root:
            raise ArithmeticError("parameter failed an original cover equation")
    return t


def curve(index):
    try:
        t = parent_parameter(index)
        E = EllipticCurve(QQ, [0, 0, 0, _A4(t), _A6(t)])
        return E if E.discriminant() else None
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def curve_mod_p(index, p):
    try:
        n = QQ(index)
        if not n.is_integer() or not n:
            return None
        field = GF(int(p))
        coefficients = [field(QQ(c)) for c in _PAIR["auxiliary_a_invariants"]]
        auxiliary = EllipticCurve(field, coefficients)
        x, y = map(lambda value: field(QQ(value)), _PAIR["auxiliary_point"])
        T = int(n) * auxiliary(x, y)
        if not T:
            return None
        X, Y = T.xy()
        e = field(_F[0].sqrt())
        a, b, d = (field(_F[k]) for k in (4, 3, 1))
        denominator = X * X - 4 * e * e * a
        if not denominator:
            return None
        z = (2 * e * Y + X * d + 2 * e * e * b) / denominator
        def evaluate(poly, value):
            return sum((field(c) * value**i for i, c in enumerate(poly)), field(0))
        den = evaluate(_D, z)
        if not den:
            return None
        t = evaluate(_N, z) / den
        E = EllipticCurve(field, [0, 0, 0, evaluate(_A4, t), evaluate(_A6, t)])
        return E if E.discriminant() else None
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def _polynomial(coefficients, ring):
    return sum((ring(QQ(value)) * ring.gen()**i
                for i, value in enumerate(coefficients)), ring(0))


def _section_coordinate(section, coordinate, ring, value):
    numerator = ring(section[f"{coordinate}_numerator"].replace("^", "**"))
    denominator = ring(section[f"{coordinate}_denominator"].replace("^", "**"))
    return numerator(value) / denominator(value)


def _cover_section_points(index, cover_index, section_indices):
    """Evaluate exact section coordinates from the paper on a rational fiber."""
    from sage.all import PolynomialRing

    data = json.loads(Path(__file__).with_name(
        f"rank18-cover{int(cover_index)}.json").read_text())
    cover = data["quadratic_basechange"]
    ring = PolynomialRing(QQ, "U")
    parameter_numerator = _polynomial(cover["parameter_numerator"], ring)
    parameter_denominator = _polynomial(cover["parameter_denominator"], ring)
    t = parent_parameter(index)
    fiber_parameter_polynomial = parameter_numerator - t * parameter_denominator
    roots = [QQ(root) for root, _multiplicity in fiber_parameter_polynomial.roots(QQ)]
    if not roots:
        raise ArithmeticError(
            f"fiber t={t} did not split over Q on cover {cover_index}"
        )
    t_poly = _R(t)
    branch = _polynomial(cover["branch_coefficients"], _R)
    curve_at_t = EllipticCurve(QQ, [0, 0, 0, _A4(t_poly), _A6(t_poly)])
    for u in roots:
        scale = parameter_denominator(u)
        if not scale:
            continue
        branch_root = _polynomial(cover["branch_root_numerator"], ring)(u) / scale
        if branch(t) != branch_root * branch_root:
            continue
        evaluated = []
        try:
            for section_index in section_indices:
                section = data["neighbor_sections"][int(section_index)]
                x = _section_coordinate(section, "x", ring, u) / scale**4
                y = _section_coordinate(section, "y", ring, u) / scale**6
                evaluated.append(curve_at_t(x, y))
        except (ArithmeticError, ValueError, ZeroDivisionError):
            continue
        return evaluated
    raise ArithmeticError(f"could not evaluate cover {cover_index} sections at t={t}")


def generic_section_points(index):
    """Return the 19 paper sections specialized at the indexed rational point.

    This returns candidates, not a fiber-rank certificate. Rank Hunter checks
    every point and certifies independence on the specialized curve itself.
    """
    E = curve(index)
    if E is None:
        raise ValueError("family specialization is singular")
    first_cover = _cover_section_points(index, 4339, range(18))
    second_extra = _cover_section_points(index, 36773, (17,))[0]
    points = first_cover + [second_extra]
    if len(points) != 19 or any(P.curve() != E for P in points):
        raise ArithmeticError("specialized paper sections do not lie on the family fiber")
    return points


def validate_generic_rank_claim():
    """Replay the bundled algebraic map and the two Gram independence receipts."""
    if (_PROOF["rank_lower_bound"] != 19 or _PROOF["parameter_base_genus"] != 1
            or _PROOF["status"] != "certified_generic_lower_bound"
            or _PAIR["cover_indices"] != [4339, 36773]):
        raise ArithmeticError("paired-cover certificate metadata changed")
    q1, q2 = map(_R, _DATA["cover_coefficients"])
    if (_N.gcd(_D).degree() != 0 or q1.gcd(q2).degree() != 0
            or any(q.degree() != 2 or q.gcd(q.derivative()).degree() != 0 for q in (q1, q2))):
        raise ArithmeticError("cover branch equations are not independent quadratics")
    if q1[2]*_N*_N + q1[1]*_N*_D + q1[0]*_D*_D != _W*_W:
        raise ArithmeticError("first cover map failed")
    if q2[2]*_N*_N + q2[1]*_N*_D + q2[0]*_D*_D != _F:
        raise ArithmeticError("second cover map failed")
    if _F.degree() != 4 or _F.gcd(_F.derivative()).degree() != 0:
        raise ArithmeticError("auxiliary quartic is not smooth genus one")
    parent = matrix(QQ, _DATA["parent_height_matrix"])
    if parent.nrows() != 17 or not parent.is_positive_definite():
        raise ArithmeticError("parent rank-17 Gram failed")
    for receipt in _PROOF["section_gram_receipts"]:
        model_path = Path(__file__).with_name(
            f"rank18-cover{receipt['cover_index']}.json")
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != receipt["rank18_model_sha256"]:
            raise ArithmeticError("bundled rank-18 construction differs from its proof")
        gram = matrix(QQ, receipt["gram"])
        if (gram.nrows() != 18 or not gram.is_positive_definite()
                or gram[:17, :17] != 2 * parent
                or gram.det() != QQ(receipt["determinant"])):
            raise ArithmeticError("rank-18 lift Gram failed")
    auxiliary = EllipticCurve(QQ, _PAIR["auxiliary_a_invariants"])
    P = auxiliary(*map(QQ, _PAIR["auxiliary_point"]))
    torsion_bound = 0
    for prime, recorded_order in _PAIR["reduction_orders"]:
        if (not ZZ(prime).is_prime()
                or auxiliary.discriminant().numerator() % prime == 0
                or any(a.denominator() % prime == 0 for a in auxiliary.a_invariants())):
            raise ArithmeticError("invalid auxiliary reduction prime")
        actual_order = int(auxiliary.change_ring(GF(prime)).cardinality())
        if actual_order != recorded_order:
            raise ArithmeticError("auxiliary reduction order changed")
        torsion_bound = gcd(torsion_bound, actual_order)
    if (torsion_bound != int(_PROOF["auxiliary_torsion_order_multiple"])
            or not torsion_bound * P):
        raise ArithmeticError("recorded point is not proven infinite order")
    return {"verified": True, "lower_bound": 19,
            "base_field": _PROOF["base_field"], "parameter_base_genus": 1,
            "specialized_rank_claim": None,
            "source_proof_sha256": _DATA["source_proof_sha256"]}
