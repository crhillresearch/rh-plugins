"""Campbell-local numerical subgroup scheduling helpers.

These routines rank already exact rational points for *scheduling* only.  They
never certify Mordell--Weil independence and never change a rigorous rank
bound.  Exact promotion remains the responsibility of rank42.exact_lb.

The helpers used to live in an experimental Rank Hunter core module that is no
longer part of the public v0.8.7.1 core.  They are deliberately small and
plugin-local because this screening policy is Campbell-search behavior, not a
core contract.
"""

from __future__ import annotations

from fractions import Fraction
import math


def _q(value):
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _point_key(point):
    """Deterministic finite-point key, identifying the Campbell +/- pair."""
    x = _q(point[0])
    y = _q(point[1])
    if y < 0:
        y = -y
    return str(x), str(y)


def _height_key(point):
    """Cheap exact ordering key used only to spread numerical screen work."""
    x = _q(point[0])
    y = _q(point[1])
    hx = max(abs(x.numerator), x.denominator)
    hy = max(abs(y.numerator), y.denominator)
    return max(hx, hy), hx, hy, x.denominator, y.denominator, _point_key(point)


def spread_points(points, count):
    """Return at most ``count`` unique points spread across exact height order.

    Selection is deterministic.  It is only a work-scheduling heuristic: no
    scientific claim depends on whether a point is selected by this routine.
    """
    count = max(0, int(count))
    if count == 0:
        return []

    unique = {}
    for point in points:
        unique.setdefault(_point_key(point), point)
    ordered = sorted(unique.values(), key=_height_key)
    n = len(ordered)
    if n <= count:
        return ordered
    if count == 1:
        return [ordered[0]]

    # Evenly sample the full small-to-large exact-height range, including both
    # endpoints. Integer arithmetic avoids platform-dependent roundoff.
    idxs = []
    for i in range(count):
        idx = (i * (n - 1) + (count - 1) // 2) // (count - 1)
        if not idxs or idx != idxs[-1]:
            idxs.append(idx)
    # The formula above is unique for count <= n, but retain a defensive fill.
    if len(idxs) < count:
        used = set(idxs)
        for idx in range(n):
            if idx not in used:
                idxs.append(idx)
                used.add(idx)
                if len(idxs) == count:
                    break
        idxs.sort()
    return [ordered[idx] for idx in idxs[:count]]


def _solve(matrix, rhs):
    """Solve a small floating-point linear system by pivoted elimination."""
    n = len(rhs)
    if n == 0:
        return []
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("basis Gram block is not square")

    aug = [[float(matrix[i][j]) for j in range(n)] + [float(rhs[i])] for i in range(n)]
    scale = max(1.0, max(abs(v) for row in aug for v in row[:-1]))
    tol = 1e-12 * scale

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) <= tol:
            raise ValueError("basis Gram block is numerically singular")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        piv = aug[col][col]
        for row in range(col + 1, n):
            factor = aug[row][col] / piv
            if factor == 0.0:
                continue
            aug[row][col] = 0.0
            for j in range(col + 1, n + 1):
                aug[row][j] -= factor * aug[col][j]

    out = [0.0] * n
    for row in range(n - 1, -1, -1):
        rhs_value = aug[row][n] - sum(aug[row][j] * out[j] for j in range(row + 1, n))
        piv = aug[row][row]
        if abs(piv) <= tol:
            raise ValueError("basis Gram block is numerically singular")
        out[row] = rhs_value / piv
    return out


def projection_residuals(gram, basis_count):
    """Return numerical Neron--Tate residuals outside the supplied basis span.

    ``gram`` is the height-pairing Gram matrix for ``basis + candidates``.
    For each candidate P this computes the Schur-complement quantity

        <P,P> - v^T G_basis^{-1} v,

    and its ratio to <P,P>.  Tiny negative values caused by floating-point
    roundoff are clamped to zero.  Materially negative values are rejected as
    an invalid numerical screen.
    """
    rows = [[float(v) for v in row] for row in gram]
    n = len(rows)
    if any(len(row) != n for row in rows):
        raise ValueError("height Gram matrix is not square")
    basis_count = int(basis_count)
    if basis_count < 0 or basis_count > n:
        raise ValueError("basis_count is outside the Gram matrix")

    basis_gram = [row[:basis_count] for row in rows[:basis_count]]
    out = []
    for idx in range(basis_count, n):
        height = float(rows[idx][idx])
        if not math.isfinite(height) or height < 0.0:
            raise ValueError("candidate canonical height is invalid")
        if basis_count:
            cross = [float(rows[j][idx]) for j in range(basis_count)]
            coeffs = _solve(basis_gram, cross)
            projected = sum(c * x for c, x in zip(cross, coeffs))
        else:
            projected = 0.0
        residual = height - projected
        scale = max(1.0, abs(height), abs(projected))
        if residual < 0.0 and abs(residual) <= 1e-10 * scale:
            residual = 0.0
        elif residual < 0.0:
            raise ValueError("height projection produced a materially negative residual")
        relative = residual / height if height > 0.0 else 0.0
        if relative < 0.0 and abs(relative) <= 1e-12:
            relative = 0.0
        out.append({
            "height": height,
            "projected_height": projected,
            "residual": residual,
            "relative_residual": relative,
        })
    return out


def rank_novelty(records):
    """Order screen records by descending relative/absolute residual."""
    def key(rec):
        rel = rec.get("relative_residual")
        residual = rec.get("residual")
        height = rec.get("height")
        try:
            point_key = _point_key(rec["point"])
        except Exception:
            point_key = (str(rec.get("x", "")), str(rec.get("y", "")))
        return (
            -(float(rel) if rel is not None else -1.0),
            -(float(residual) if residual is not None else -1.0),
            -(float(height) if height is not None else -1.0),
            point_key,
        )
    return sorted(records, key=key)
