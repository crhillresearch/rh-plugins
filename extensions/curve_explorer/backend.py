"""Exact arithmetic and visualization data for Rank Hunter Curve Explorer v0.4.4.

Scientific boundary
-------------------
Point arithmetic, secants/tangents, third intersections, and negation are exact
over Q using ``fractions.Fraction``. The continuous real-locus plot and screen
coordinates are floating-point visualization only; they are not rank evidence or
a certification step.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
import math
from typing import Iterable

INF = None


def Q(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    text = str(value).strip()
    if not text:
        raise ValueError("empty rational")
    return Fraction(text)


def _int_decimal(value: int) -> str:
    """Return an exact base-10 integer string without Python's digit-limit path.

    Python 3.11+ limits direct ``str(int)`` conversion for very large decimal
    integers. Elliptic-curve multiples can legitimately exceed that threshold,
    so format in small base-10 chunks instead of changing the process-global
    ``sys.set_int_max_str_digits`` setting.
    """
    value = int(value)
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    value = abs(value)
    base = 10**9
    chunks = []
    while value:
        value, chunk = divmod(value, base)
        chunks.append(chunk)
    head = str(chunks.pop())
    tail = "".join(f"{chunk:09d}" for chunk in reversed(chunks))
    return sign + head + tail


def qstr(value: Fraction) -> str:
    value = Q(value)
    numerator = _int_decimal(value.numerator)
    if value.denominator == 1:
        return numerator
    return f"{numerator}/{_int_decimal(value.denominator)}"


def safe_float(value: Fraction, *, limit: float = 1e290) -> float:
    """Convert an exact rational to a finite plotting float with saturation."""
    value = Q(value)
    try:
        out = float(value)
    except OverflowError:
        return math.copysign(limit, value.numerator)
    if not math.isfinite(out):
        return math.copysign(limit, value.numerator)
    return max(-limit, min(limit, out))


@dataclass(frozen=True)
class WeierstrassModel:
    a1: Fraction
    a2: Fraction
    a3: Fraction
    a4: Fraction
    a6: Fraction

    @classmethod
    def from_json(cls, raw: str | list | tuple) -> "WeierstrassModel":
        vals = json.loads(raw) if isinstance(raw, str) else list(raw)
        if len(vals) != 5:
            raise ValueError(f"expected five a-invariants, got {len(vals)}")
        return cls(*(Q(v) for v in vals))

    def as_strings(self):
        return [qstr(x) for x in (self.a1, self.a2, self.a3, self.a4, self.a6)]

    def rhs(self, x: Fraction) -> Fraction:
        x = Q(x)
        return x**3 + self.a2*x**2 + self.a4*x + self.a6

    def y_discriminant(self, x: Fraction) -> Fraction:
        x = Q(x)
        linear = self.a1*x + self.a3
        return linear**2 + 4*self.rhs(x)

    def on_curve(self, point) -> bool:
        if point is INF:
            return True
        x, y = point
        x, y = Q(x), Q(y)
        return y*y + self.a1*x*y + self.a3*y == self.rhs(x)

    def negate(self, point):
        if point is INF:
            return INF
        x, y = point
        x, y = Q(x), Q(y)
        return (x, -y - self.a1*x - self.a3)

    def add(self, P, Qp):
        """Exact group law on the generalized Weierstrass model."""
        if P is INF:
            return Qp
        if Qp is INF:
            return P
        x1, y1 = Q(P[0]), Q(P[1])
        x2, y2 = Q(Qp[0]), Q(Qp[1])
        if not self.on_curve((x1, y1)) or not self.on_curve((x2, y2)):
            raise ValueError("point is not on stored Weierstrass model")

        if x1 == x2 and y1 + y2 + self.a1*x1 + self.a3 == 0:
            return INF

        if x1 != x2:
            lam = (y2-y1)/(x2-x1)
            nu = (y1*x2-y2*x1)/(x2-x1)
        else:
            den = 2*y1 + self.a1*x1 + self.a3
            if den == 0:
                return INF
            lam = (3*x1*x1 + 2*self.a2*x1 + self.a4 - self.a1*y1)/den
            nu = (-x1**3 + self.a4*x1 + 2*self.a6 - self.a3*y1)/den

        x3 = lam*lam + self.a1*lam - self.a2 - x1 - x2
        y3 = -(lam + self.a1)*x3 - nu - self.a3
        result = (x3, y3)
        if not self.on_curve(result):
            raise ArithmeticError("internal group-law result failed exact curve check")
        return result

    def line_through(self, P, Qp):
        """Return exact secant/tangent y=lambda*x+nu, or None for vertical."""
        if P is INF or Qp is INF:
            return None
        x1, y1 = Q(P[0]), Q(P[1])
        x2, y2 = Q(Qp[0]), Q(Qp[1])
        if x1 == x2 and y1 + y2 + self.a1*x1 + self.a3 == 0:
            return None
        if x1 != x2:
            lam = (y2-y1)/(x2-x1)
            nu = (y1*x2-y2*x1)/(x2-x1)
        else:
            den = 2*y1 + self.a1*x1 + self.a3
            if den == 0:
                return None
            lam = (3*x1*x1 + 2*self.a2*x1 + self.a4 - self.a1*y1)/den
            nu = (-x1**3 + self.a4*x1 + 2*self.a6 - self.a3*y1)/den
        return lam, nu

    def mul(self, n: int, P):
        n = int(n)
        if n == 0 or P is INF:
            return INF
        if n < 0:
            return self.mul(-n, self.negate(P))
        result = INF
        addend = P
        while n:
            if n & 1:
                result = self.add(result, addend)
            addend = self.add(addend, addend)
            n >>= 1
        return result

    def equation_text(self) -> str:
        def term(c, symbol):
            c = Q(c)
            if not c:
                return ""
            sign = "+" if c > 0 else "−"
            ac = abs(c)
            coeff = "" if ac == 1 and symbol else qstr(ac)
            return f" {sign} {coeff}{symbol}"
        lhs = "y²" + term(self.a1, "xy") + term(self.a3, "y")
        rhs = "x³" + term(self.a2, "x²") + term(self.a4, "x") + term(self.a6, "")
        return f"{lhs} = {rhs}"


@dataclass(frozen=True)
class PointRecord:
    id: str
    x: Fraction
    y: Fraction
    role: str = "candidate"
    independence_status: str = "unknown"
    exact_verified: bool = False
    source: str = "stored"
    rigorous_independent: bool = False

    @property
    def point(self):
        return (self.x, self.y)

    @property
    def label(self):
        return f"P{self.id}"

    def compact(self):
        return f"({qstr(self.x)}, {qstr(self.y)})"

    @property
    def is_generator(self) -> bool:
        text = f"{self.role} {self.source}".lower()
        return any(token in text for token in ("generator", "basis"))

    @property
    def in_selected_subgroup(self) -> bool:
        status = self.independence_status.lower().replace("-", "_").replace(" ", "_")
        role = self.role.lower()
        return (
            self.rigorous_independent
            or self.is_generator
            or status in {"independent", "rigorous_independent", "certified", "proven_independent"}
            or any(token in role for token in ("known_section", "section_basis", "mw_basis"))
        )


def _decode_generators(raw) -> list[tuple[Fraction, Fraction]]:
    if not raw:
        return []
    try:
        values = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    out = []
    for item in values or []:
        if isinstance(item, dict) and "x" in item and "y" in item:
            out.append((Q(item["x"]), Q(item["y"])))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((Q(item[0]), Q(item[1])))
    return out


def load_curve(db, curve_id: int):
    raw = db.execute("SELECT * FROM curves WHERE id=?", (int(curve_id),)).fetchone()
    if raw is None:
        raise KeyError(f"curve #{curve_id} not found")
    row = dict(raw)
    if not row.get("a_invariants_json"):
        raise ValueError(f"curve #{curve_id} has no stored a-invariants")
    model = WeierstrassModel.from_json(row["a_invariants_json"])
    return row, model


def load_points(db, curve_id: int, model: WeierstrassModel) -> list[PointRecord]:
    records = []
    try:
        rows = db.execute(
            """SELECT * FROM points WHERE curve_id=?
               ORDER BY rigorous_independent DESC, exact_verified DESC, id ASC""",
            (int(curve_id),),
        ).fetchall()
    except Exception:
        rows = []
    for raw in rows:
        try:
            row = dict(raw)
            rec = PointRecord(
                str(row.get("id")), Q(row.get("x")), Q(row.get("y")),
                str(row.get("role") or "candidate"),
                str(row.get("independence_status") or "unknown"),
                bool(row.get("exact_verified")), str(row.get("source") or "stored"),
                bool(row.get("rigorous_independent")),
            )
            if model.on_curve(rec.point):
                records.append(rec)
        except Exception:
            continue

    if records:
        return records

    curve = db.execute("SELECT generators_json FROM curves WHERE id=?", (int(curve_id),)).fetchone()
    curve = dict(curve) if curve is not None else None
    for index, (x, y) in enumerate(_decode_generators(curve.get("generators_json") if curve else None), 1):
        if model.on_curve((x, y)):
            records.append(PointRecord(
                f"g{index}", x, y, role="legacy_generator", exact_verified=True,
                source="generators_json", rigorous_independent=True,
            ))
    return records


def rigorous_lower(row):
    values = [row[k] for k in ("exact_rank", "descent_lower", "generic_lower") if k in row and row[k] is not None]
    return max(int(v) for v in values) if values else None


def _finite_numbers(values: Iterable[float]):
    return [v for v in values if math.isfinite(v) and abs(v) < 1e290]


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("empty values")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values)-1) * max(0.0, min(1.0, q))
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    w = pos - lo
    return sorted_values[lo]*(1-w) + sorted_values[hi]*w


def _padded_bounds(xs: list[float], *, robust: bool) -> tuple[float, float]:
    xs = sorted(_finite_numbers(xs))
    if not xs:
        return (-5.0, 5.0)
    if robust and len(xs) >= 8:
        lo, hi = _quantile(xs, .10), _quantile(xs, .90)
        # If most points are identical or ultra-clustered, fall back to all.
        if not hi > lo:
            lo, hi = xs[0], xs[-1]
    else:
        lo, hi = xs[0], xs[-1]
    span = hi-lo
    if not span:
        span = max(2.0, abs(lo)*.35)
    pad = max(1.0, span*.30)
    return lo-pad, hi+pad


def coefficient_shape_bounds(model: WeierstrassModel) -> tuple[float, float]:
    """Coefficient-informed x window for viewing topology, not arithmetic."""
    coeff = [abs(safe_float(x)) for x in (model.a1, model.a2, model.a3, model.a4, model.a6)]
    scales = [3.0]
    if coeff[0] > 0: scales.append(coeff[0]**2)
    if coeff[1] > 0: scales.append(coeff[1])
    if coeff[2] > 0: scales.append(coeff[2]**(2/3))
    if coeff[3] > 0: scales.append(coeff[3]**0.5)
    if coeff[4] > 0: scales.append(coeff[4]**(1/3))
    scale = max(3.0, min(max(scales), 1e12))
    return -2.2*scale, 2.2*scale


def choose_bounds(model: WeierstrassModel, points: list[PointRecord], selected: list[PointRecord] | None = None, mode: str = "Smart"):
    """Choose a useful initial x window; Y is computed client-side from the locus.

    ``Smart`` deliberately ignores extreme outliers when a curve has many stored
    points. The graph still exposes an explicit ``Fit all`` control.
    """
    selected = list(selected or [])
    mode = str(mode or "Smart")
    if mode == "Selected points" and selected:
        return _padded_bounds([safe_float(p.x) for p in selected], robust=False)
    if mode == "All stored points" and points:
        return _padded_bounds([safe_float(p.x) for p in points], robust=False)
    if mode == "Smart" and points:
        return _padded_bounds([safe_float(p.x) for p in points], robust=True)
    return coefficient_shape_bounds(model)


def _point_payload(p: PointRecord, *, interactive: bool) -> dict:
    return {
        "id": str(p.id), "label": p.label,
        "x": safe_float(p.x), "y": safe_float(p.y),
        "x_exact": qstr(p.x), "y_exact": qstr(p.y),
        "role": p.role, "independence": p.independence_status,
        "exact_verified": bool(p.exact_verified),
        "rigorous_independent": bool(p.rigorous_independent),
        "is_generator": bool(p.is_generator),
        "in_subgroup": bool(p.in_selected_subgroup),
        "interactive": bool(interactive),
    }


def exact_pair_constructions(model: WeierstrassModel, points: list[PointRecord], *, max_points: int = 96):
    """Precompute exact P,Q -> R -> -R data for browser click interaction.

    The bounded cache prevents huge HTML payloads on curves with thousands of
    mapped points. Points are already ordered with rigorous/verified points first.
    """
    cap = max(0, min(int(max_points), len(points)))
    active = points[:cap]
    out = {}
    for i, P in enumerate(active):
        for Qp in active[i:]:
            key = "|".join(sorted((str(P.id), str(Qp.id))))
            line = model.line_through(P.point, Qp.point)
            result = model.add(P.point, Qp.point)
            item = {
                "p": str(P.id), "q": str(Qp.id),
                "vertical": line is None,
                "x_vertical": safe_float(P.x) if line is None else None,
                "line": None,
                "result": None,
                "third": None,
            }
            if line is not None:
                item["line"] = {
                    "lambda": safe_float(line[0]), "nu": safe_float(line[1]),
                    "lambda_exact": qstr(line[0]), "nu_exact": qstr(line[1]),
                }
            if result is not INF:
                third = model.negate(result)
                item["result"] = {
                    "x": safe_float(result[0]), "y": safe_float(result[1]),
                    "x_exact": qstr(result[0]), "y_exact": qstr(result[1]),
                }
                item["third"] = {
                    "x": safe_float(third[0]), "y": safe_float(third[1]),
                    "x_exact": qstr(third[0]), "y_exact": qstr(third[1]),
                }
            out[key] = item
    return out, cap


def plot_payload(model: WeierstrassModel, points: list[PointRecord], *, bounds=(-5.0, 5.0),
                 samples=2200, pair_cache_points=96):
    pairs, cap = exact_pair_constructions(model, points, max_points=pair_cache_points)
    return {
        "ainv": [safe_float(x) for x in (model.a1, model.a2, model.a3, model.a4, model.a6)],
        "ainv_exact": model.as_strings(),
        "equation": model.equation_text(),
        "points": [_point_payload(p, interactive=(i < cap)) for i, p in enumerate(points)],
        "pair_constructions": pairs,
        "pair_cache_points": cap,
        "point_count": len(points),
        "xmin": float(bounds[0]), "xmax": float(bounds[1]),
        "shape_bounds": list(coefficient_shape_bounds(model)),
        "samples": max(500, min(6000, int(samples))),
    }
