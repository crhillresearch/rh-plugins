"""Exact torsion/PGL2 symmetry utilities for Rank Hunter search coordinates.

The mathematical input is the equivariance principle used by Faugere--Huot--
Joux--Renault--Vitse: for a degree-2 map phi:E->P1 and rational 2-torsion T,
translation by T induces a PGL2 action on the chosen P1 coordinate.

This module is intentionally pure Python and exact over Q.  It does *not* infer
that an action on one coordinate (for example Weierstrass x) is automatically an
action on a different coordinate (for example a native quartic x).  For a native
quartic, provide/recover the action in that native coordinate before reducing
charts.
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt, lcm
from pathlib import Path
from typing import Any, Iterable
import json

SCHEMA = "rank-hunter-torsion-symmetry-v1"


class SymmetryError(ValueError):
    pass


def q(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise SymmetryError("boolean is not a rational number")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value.strip())
        except Exception as exc:
            raise SymmetryError(f"invalid exact rational: {value!r}") from exc
    if isinstance(value, float):
        raise SymmetryError("floating-point inputs are rejected; use an integer or exact 'p/q' string")
    try:
        return Fraction(value)
    except Exception as exc:
        raise SymmetryError(f"invalid exact rational: {value!r}") from exc


def qstr(x: Fraction | int) -> str:
    x = q(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _divisors(n: int) -> list[int]:
    n = abs(int(n))
    if n == 0:
        return [0]
    small, large = [], []
    for d in range(1, isqrt(n) + 1):
        if n % d == 0:
            small.append(d)
            if d * d != n:
                large.append(n // d)
    return small + large[::-1]


def _primitive_integer_poly(coeffs_low: Iterable[Fraction]) -> list[int]:
    coeffs = [q(x) for x in coeffs_low]
    den = 1
    for x in coeffs:
        den = lcm(den, x.denominator)
    vals = [int(x * den) for x in coeffs]
    g = 0
    for x in vals:
        g = gcd(g, abs(x))
    if g:
        vals = [x // g for x in vals]
    while len(vals) > 1 and vals[-1] == 0:
        vals.pop()
    if vals and vals[-1] < 0:
        vals = [-x for x in vals]
    return vals


def eval_poly(coeffs_low: Iterable[Fraction], x: Fraction) -> Fraction:
    acc = Fraction(0)
    for c in reversed([q(v) for v in coeffs_low]):
        acc = acc * x + c
    return acc


def rational_roots_cubic_monic(a2: Any, a4: Any, a6: Any) -> list[Fraction]:
    """Rational roots of x^3+a2*x^2+a4*x+a6, exactly.

    The routine uses the rational-root theorem after clearing denominators.
    This is designed for audit-sized coefficients; callers may supply explicit
    roots in higher-level workflows if a family has enormous coefficients.
    """
    coeffs = [q(a6), q(a4), q(a2), Fraction(1)]
    ints = _primitive_integer_poly(coeffs)
    if len(ints) != 4:
        raise SymmetryError("expected a cubic polynomial")
    c0, _, _, c3 = ints
    roots: set[Fraction] = set()
    if c0 == 0:
        roots.add(Fraction(0))
        # Divide the rational polynomial by x and solve quadratic exactly.
        # For simplicity, continue with rational-root enumeration too.
    pvals = _divisors(c0) if c0 else [0]
    qvals = _divisors(c3)
    if c0 == 0:
        # roots of remaining quadratic are still roots p/q with p dividing the
        # first nonzero lower coefficient, so enumerate a modest exact fallback.
        fallback = next((abs(v) for v in ints[:-1] if v), 1)
        pvals = [0] + _divisors(fallback)
    for p in pvals:
        for d in qvals:
            if d == 0:
                continue
            candidates = [Fraction(0)] if p == 0 else [Fraction(p, d), Fraction(-p, d)]
            for r in candidates:
                if eval_poly(coeffs, r) == 0:
                    roots.add(r)
    return sorted(roots)


# PGL2 matrices are tuples (a,b,c,d) representing (a*x+b)/(c*x+d).

def matrix4(raw: Any) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    if isinstance(raw, dict):
        if "matrix" in raw:
            raw = raw["matrix"]
        elif all(k in raw for k in ("A", "B", "C", "D")):
            raw = [raw["A"], raw["B"], raw["C"], raw["D"]]
        elif all(k in raw for k in ("a", "b", "c", "d")):
            raw = [raw["a"], raw["b"], raw["c"], raw["d"]]
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        raise SymmetryError("PGL2 matrix must be [a,b,c,d]")
    m = tuple(q(x) for x in raw)
    if m[0] * m[3] - m[1] * m[2] == 0:
        raise SymmetryError("singular PGL2 matrix")
    return m  # type: ignore[return-value]


def matrix_signature(raw: Any) -> tuple[int, int, int, int]:
    vals = list(matrix4(raw))
    den = 1
    for x in vals:
        den = lcm(den, x.denominator)
    ints = [int(x * den) for x in vals]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    if g:
        ints = [x // g for x in ints]
    for x in ints:
        if x:
            if x < 0:
                ints = [-v for v in ints]
            break
    return tuple(ints)  # type: ignore[return-value]


def signature_strings(sig: tuple[int, int, int, int]) -> list[str]:
    return [str(int(x)) for x in sig]


def compose(left: Any, right: Any) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    """Return left ∘ right."""
    a,b,c,d = matrix4(left)
    e,f,g,h = matrix4(right)
    return (a*e+b*g, a*f+b*h, c*e+d*g, c*f+d*h)


def inverse(raw: Any) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    a,b,c,d = matrix4(raw)
    return (d, -b, -c, a)


def apply_pgl2(raw: Any, x: Fraction | None) -> Fraction | None:
    """Apply to Q∪{∞}; None denotes infinity."""
    a,b,c,d = matrix4(raw)
    if x is None:
        return None if c == 0 else a/c
    x = q(x)
    den = c*x+d
    if den == 0:
        return None
    return (a*x+b)/den


def group_closure(generators: Iterable[Any], *, max_order: int = 64) -> list[tuple[int,int,int,int]]:
    identity = (1,0,0,1)
    seen = {identity}
    queue = [identity]
    gens = [matrix_signature(g) for g in generators]
    for g in gens:
        seen.add(g)
        queue.append(g)
    while queue:
        x = queue.pop(0)
        current = list(seen)
        for y in current + gens:
            for z in (compose(x,y), compose(y,x)):
                s = matrix_signature(z)
                if s not in seen:
                    seen.add(s)
                    queue.append(s)
                    if len(seen) > max_order:
                        raise SymmetryError(f"generated PGL2 group exceeded safety cap {max_order}")
    return sorted(seen)


def weierstrass_2torsion_action(root: Any, a2: Any, a4: Any) -> tuple[int,int,int,int]:
    """PGL2 action on x for T=(r,0) on y²=x³+a2*x²+a4*x+a6.

    With r a root and B=f'(r), x(P+T)=r+B/(x(P)-r).
    """
    r, a2, a4 = q(root), q(a2), q(a4)
    B = 3*r*r + 2*a2*r + a4
    if B == 0:
        raise SymmetryError("singular cubic/root: f'(r)=0")
    # r + B/(x-r) = (r*x + B-r^2)/(x-r)
    return matrix_signature((r, B-r*r, 1, -r))


def audit_weierstrass_2torsion(curve: dict[str, Any]) -> dict[str, Any]:
    model = curve.get("model", "y2=x3+a2x2+a4x+a6")
    if model not in {"y2=x3+a2x2+a4x+a6", "weierstrass-cubic"}:
        raise SymmetryError("this exact automatic mode currently expects y^2=x^3+a2*x^2+a4*x+a6")
    a2, a4, a6 = q(curve.get("a2", 0)), q(curve.get("a4", 0)), q(curve.get("a6", 0))
    roots = rational_roots_cubic_monic(a2,a4,a6)
    actions = []
    for r in roots:
        sig = weierstrass_2torsion_action(r,a2,a4)
        actions.append({
            "torsion_x": qstr(r),
            "order": 2,
            "pgl2_matrix": signature_strings(sig),
            "formula": f"x -> ({sig[0]}*x+({sig[1]}))/({sig[2]}*x+({sig[3]}))",
        })
    group = group_closure([a["pgl2_matrix"] for a in actions]) if actions else [(1,0,0,1)]
    return {
        "schema": SCHEMA,
        "mode": "weierstrass-x",
        "curve": {"a2": qstr(a2), "a4": qstr(a4), "a6": qstr(a6)},
        "rational_nonzero_2torsion_points": len(roots),
        "rational_2torsion_x": [qstr(r) for r in roots],
        "actions": actions,
        "generated_action_group_order": len(group),
        "generated_action_group": [signature_strings(g) for g in group],
        "claim_boundary": (
            "Exact PGL2 action on this Weierstrass x-coordinate only. Do not apply these matrices "
            "to a different degree-2 coordinate (such as a native quartic x) without exact transport/recovery."
        ),
    }


def _rref_null_vector(rows: list[list[Fraction]], ncols: int = 4) -> tuple[Fraction,...]:
    A = [list(map(q,row)) for row in rows]
    m = len(A)
    pivots: list[int] = []
    r = 0
    for c in range(ncols):
        pivot = next((i for i in range(r,m) if A[i][c] != 0), None)
        if pivot is None:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        pv = A[r][c]
        A[r] = [x/pv for x in A[r]]
        for i in range(m):
            if i != r and A[i][c] != 0:
                f = A[i][c]
                A[i] = [A[i][j]-f*A[r][j] for j in range(ncols)]
        pivots.append(c)
        r += 1
        if r == m:
            break
    free = [c for c in range(ncols) if c not in pivots]
    if len(free) != 1:
        raise SymmetryError(f"sample equations do not determine a unique PGL2 map up to scale (nullity={len(free)})")
    fcol = free[0]
    v = [Fraction(0)]*ncols
    v[fcol] = Fraction(1)
    for rr, pc in reversed(list(enumerate(pivots))):
        v[pc] = -sum(A[rr][j]*v[j] for j in free)
    if all(x == 0 for x in v):
        raise SymmetryError("failed to recover nonzero PGL2 vector")
    return tuple(v)


def recover_pgl2_from_samples(samples: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Recover y=(a*x+b)/(c*x+d) from >=3 exact finite sample pairs."""
    pairs = []
    for rec in samples:
        if not isinstance(rec, dict):
            raise SymmetryError("each sample must be an object with x and image")
        x = q(rec["x"])
        y = q(rec.get("image", rec.get("x_image")))
        pairs.append((x,y))
    if len(pairs) < 3:
        raise SymmetryError("need at least three exact sample pairs")
    rows = [[x, Fraction(1), -y*x, -y] for x,y in pairs[:3]]
    raw = _rref_null_vector(rows)
    sig = matrix_signature(raw)
    failures = []
    for i,(x,y) in enumerate(pairs,1):
        got = apply_pgl2(sig,x)
        if got != y:
            failures.append({"sample": i, "x": qstr(x), "expected": qstr(y), "got": None if got is None else qstr(got)})
    if failures:
        raise SymmetryError(f"recovered map failed {len(failures)} supplied verification samples")
    return {
        "schema": SCHEMA,
        "status": "exact-recovered",
        "samples_verified": len(pairs),
        "pgl2_matrix": signature_strings(sig),
        "claim_boundary": "Exact PGL2 relation for the supplied coordinate samples; the caller is responsible for proving those samples arise from the intended torsion translation.",
    }


def _chart_matrix(rec: Any) -> tuple[Fraction,Fraction,Fraction,Fraction]:
    if isinstance(rec, dict):
        if "matrix" in rec:
            return matrix4(rec["matrix"])
        meta = rec.get("chart")
        if isinstance(meta, dict) and "matrix" in meta:
            return matrix4(meta["matrix"])
    return matrix4(rec)


def reduce_chart_orbits(charts: Iterable[Any], actions: Iterable[Any], *, coordinate_label: str = "native-x") -> dict[str, Any]:
    """Group charts under left composition by an exact PGL2 symmetry group.

    Chart convention: x=(A*z+B)/(C*z+D).  If g acts on the *same* x-coordinate,
    the torsion-equivalent chart is g∘M.  No equivalence in the z/source side is
    assumed.
    """
    chart_list = list(charts)
    if not chart_list:
        raise SymmetryError("at least one chart is required")
    group = group_closure(actions)
    records = []
    for i, rec in enumerate(chart_list):
        M = _chart_matrix(rec)
        sig = matrix_signature(M)
        orbit = sorted({matrix_signature(compose(g,M)) for g in group})
        orbit_key = min(orbit)
        chart_id = rec.get("id") if isinstance(rec,dict) else None
        if chart_id is None and isinstance(rec,dict):
            chart_id = rec.get("chart_id") or rec.get("name")
        chart_id = str(chart_id) if chart_id is not None else f"chart-{i+1:04d}"
        records.append({
            "index": i,
            "chart_id": chart_id,
            "matrix_signature": signature_strings(sig),
            "orbit_key": signature_strings(orbit_key),
            "full_orbit_size": len(orbit),
            "original": rec,
        })
    buckets: dict[tuple[int,int,int,int], list[dict[str,Any]]] = {}
    for row in records:
        key = tuple(int(x) for x in row["orbit_key"])
        buckets.setdefault(key, []).append(row)
    orbits = []
    representatives = []
    for rank,(key,members) in enumerate(sorted(buckets.items()),1):
        # Deterministic representative: smallest matrix signature, then input order.
        rep = min(members, key=lambda r: (tuple(int(x) for x in r["matrix_signature"]), r["index"]))
        representatives.append(rep["original"])
        orbits.append({
            "orbit": rank,
            "orbit_key": signature_strings(key),
            "observed_members": len(members),
            "full_group_orbit_size": rep["full_orbit_size"],
            "representative_chart_id": rep["chart_id"],
            "member_chart_ids": [r["chart_id"] for r in sorted(members,key=lambda x:x["index"])],
            "representative_matrix": rep["matrix_signature"],
        })
    n = len(chart_list)
    u = len(orbits)
    return {
        "schema": SCHEMA,
        "status": "exact-chart-orbit-audit",
        "coordinate": coordinate_label,
        "chart_convention": "x=(A*z+B)/(C*z+D); symmetry acts by left composition g∘M",
        "input_charts": n,
        "symmetry_group_order": len(group),
        "unique_chart_orbits": u,
        "redundant_input_charts": n-u,
        "dedup_factor": round(n/u, 6),
        "searches_saved_if_one_per_observed_orbit": n-u,
        "savings_percent": round(100.0*(n-u)/n, 3),
        "orbits": orbits,
        "representatives": representatives,
        "group": [signature_strings(g) for g in group],
        "claim_boundary": (
            "This proves chart equivalence only under the supplied exact PGL2 actions on the stated coordinate. "
            "It does not prove that Weierstrass-x actions apply to a native quartic coordinate, and it does not change any rank claim."
        ),
    }


def chart_audit_from_payload(charts_payload: Any, actions_payload: Any, *, coordinate_label: str = "native-x") -> dict[str, Any]:
    charts = charts_payload.get("charts") if isinstance(charts_payload,dict) else charts_payload
    if not isinstance(charts,list):
        raise SymmetryError("charts payload must be a list or {'charts': [...]} object")
    if isinstance(actions_payload,dict):
        acts = actions_payload.get("generated_action_group") or actions_payload.get("actions") or actions_payload.get("generators")
        if acts and isinstance(acts,list) and acts and isinstance(acts[0],dict):
            acts = [x.get("pgl2_matrix") or x.get("matrix") for x in acts]
    else:
        acts = actions_payload
    if not isinstance(acts,list):
        raise SymmetryError("actions payload must supply a list of PGL2 matrices")
    return reduce_chart_orbits(charts, acts, coordinate_label=coordinate_label)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def save_json(path: str | Path, value: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
