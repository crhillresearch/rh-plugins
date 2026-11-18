"""C4 S3 family over the positive-rank genus-one splitting cover."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, sage_eval


HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "family.json").read_text(encoding="utf-8"))
PROOF = json.loads((HERE / "proof/data/construction.json").read_text(encoding="utf-8"))
WITNESS = json.loads((HERE / "proof/data/witness.json").read_text(encoding="utf-8"))

generic_rank = 6
parameter_base_genus = 1
candidate_denominator_mode = "family_owned"


def name():
    return DATA["name"]


def candidate_seed_parameters():
    return (2,)


def _selector(value):
    value = QQ(value)
    if not value.is_integer() or not value:
        raise ValueError("parameter must be a nonzero integer multiple of the base point")
    return int(value)


def parameter_point(index):
    """Map an integer multiple of the certified Jacobian point to (u, v)."""
    n = _selector(index)
    coefficients = [QQ(x) for x in PROOF["galois_quartic_low_to_high"]]
    e = QQ(coefficients[0]).sqrt()
    c0, c1, c2, c3, c4 = coefficients
    if e * e != c0:
        raise ArithmeticError("quartic seed does not lie on the base")
    J = EllipticCurve(QQ, [0, c2, 0, c3*c1 - 4*c4*e*e,
                            e*e*c3*c3 + c4*c1*c1 - 4*c4*c2*e*e])
    R = J(*[QQ(x) for x in PROOF["seed_jacobian_point_XY"]])
    point = n * R
    if point.is_zero():
        raise ValueError("the selected Jacobian multiple is the point at infinity")
    X, Y = point.xy()
    denominator = X*X - 4*c4*e*e
    if not denominator:
        raise ValueError("the selected point is outside the quartic chart")
    u = (2*e*Y + X*c1 + 2*e*e*c3) / denominator
    v = (X*u*u - c1*u) / (2*e) - e
    if v*v != sum(coefficient*u**i for i, coefficient in enumerate(coefficients)):
        raise ArithmeticError("Jacobian-to-quartic map failed")
    return u, v


def _evaluate(expression, u, v):
    return QQ(sage_eval(str(expression).replace("^", "**"), locals={"u": u, "v": v}))


def curve(index):
    try:
        u, v = parameter_point(index)
        E = EllipticCurve(QQ, [_evaluate(x, u, v) for x in DATA["a_invariants"]])
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(index, p):
    E = curve(index)
    if E is None:
        return None
    try:
        field = GF(int(p))
        reduced = EllipticCurve(field, [field(x) for x in E.a_invariants()])
        return reduced if reduced.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(index):
    E = curve(index)
    if E is None:
        raise ValueError("selected specialization is singular")
    u, v = parameter_point(index)
    return [E(_evaluate(row["x"], u, v), _evaluate(row["y"], u, v))
            for row in DATA["sections"]]


def validate_generic_rank_claim():
    """Replay the bundled Rank Ledger proof relative to the published parent theorem."""
    ring = PolynomialRing(QQ, "u")
    u = ring.gen()
    base_polynomial = ring(sage_eval(DATA["base_polynomial"].replace("^", "**"), locals={"u": u}))
    coefficients = [QQ(x) for x in PROOF["galois_quartic_low_to_high"]]
    if (int(DATA.get("parameter_base_genus") or 0) != 1
            or int(DATA.get("verified_generic_rank_lower") or 0) != 6
            or int(PROOF.get("certified_generic_rank_lower_bound") or 0) != 6
            or len(DATA.get("sections") or []) != 8
            or base_polynomial != sum(x*u**i for i, x in enumerate(coefficients))
            or [str(x) for x in WITNESS["quartic_rational_point_2R_uw"]]
               != [str(x) for x in parameter_point(2)]):
        raise ArithmeticError("packaged C4 family and proof packet disagree")
    process = subprocess.run(
        [sys.executable, str(HERE / "proof/verify.py")],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if process.returncode or "CERTIFIED relative to published EK2020" not in process.stdout:
        raise ArithmeticError("C4 S3 proof replay failed: " + (process.stderr or process.stdout)[-1000:])
    return {"verified": True, "lower_bound": 6,
            "method": "exact S3 proof replay relative to published rank-four parent theorem",
            "base_genus": 1, "torsion_subgroup": "C4"}
