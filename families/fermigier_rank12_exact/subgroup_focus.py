"""Plugin-local numerical subgroup scheduling helpers.

These helpers deliberately produce *screening* evidence only.  They never
certify Mordell--Weil independence or change a rigorous rank bound.

Rank Hunter keeps the generic height worker in core, while the
Fermigier search owns the policy for selecting candidate points and ranking
projection residuals.  Keeping that policy here avoids a dependency on the
retired ``rank42.subgroup_focus_core`` module.
"""

from __future__ import annotations

import math
from fractions import Fraction


def _fraction(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    return Fraction(str(value))


def _point_key(point):
    """Deterministic affine key, identifying P and -P for scheduling."""
    x = _fraction(point[0])
    y = _fraction(point[1])
    if y < 0:
        y = -y
    return x, y


def _rational_height_key(value):
    q = _fraction(value)
    return max(abs(q.numerator), q.denominator), q.denominator, abs(q.numerator), q


def spread_points(points, limit):
    """Return a deterministic height-spread subset of exact affine points.

    The point set is first deduplicated up to ``P -> -P`` and ordered by the
    rational height of x (then y for deterministic ties).  When truncation is
    required, evenly spaced positions across that ordered range are retained
    rather than keeping only the easiest/smallest points.
    """
    limit = max(0, int(limit))
    if limit == 0:
        return []

    unique = {}
    for point in points:
        key = _point_key(point)
        unique.setdefault(key, point)
    ordered = sorted(
        unique.values(),
        key=lambda p: (_rational_height_key(p[0]), _rational_height_key(p[1])),
    )
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]

    indexes = []
    for i in range(limit):
        idx = round(i * (len(ordered) - 1) / (limit - 1))
        if idx not in indexes:
            indexes.append(idx)
    return [ordered[i] for i in indexes]


def _as_square_float_matrix(gram):
    matrix = [[float(value) for value in row] for row in gram]
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("height Gram matrix must be square")
    if any(not math.isfinite(value) for row in matrix for value in row):
        raise ValueError("height Gram matrix contains non-finite values")
    return matrix


def _cholesky(matrix, *, rel_tol=1e-12):
    """Cholesky factor of a numerically positive-definite symmetric matrix."""
    n = len(matrix)
    if n == 0:
        return []
    scale = max(1.0, max(abs(matrix[i][i]) for i in range(n)))
    symmetry_tol = rel_tol * scale * 10.0
    for i in range(n):
        for j in range(i):
            if abs(matrix[i][j] - matrix[j][i]) > symmetry_tol:
                raise ValueError("height basis Gram matrix is not numerically symmetric")

    L = [[0.0] * n for _ in range(n)]
    pivot_tol = rel_tol * scale
    for i in range(n):
        pivot = matrix[i][i] - sum(L[i][k] * L[i][k] for k in range(i))
        if not math.isfinite(pivot) or pivot <= pivot_tol:
            raise ValueError("height basis Gram matrix is not numerically positive definite")
        L[i][i] = math.sqrt(pivot)
        for j in range(i + 1, n):
            numer = matrix[j][i] - sum(L[j][k] * L[i][k] for k in range(i))
            L[j][i] = numer / L[i][i]
    return L


def _solve_cholesky(L, vector):
    n = len(L)
    if len(vector) != n:
        raise ValueError("projection vector has wrong dimension")
    if n == 0:
        return []

    y = [0.0] * n
    for i in range(n):
        y[i] = (vector[i] - sum(L[i][k] * y[k] for k in range(i))) / L[i][i]

    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(L[k][i] * x[k] for k in range(i + 1, n))) / L[i][i]
    return x


def projection_residuals(gram, basis_count):
    """Compute numerical candidate residuals modulo the supplied basis.

    For each candidate P, with height h and pairing vector v against the basis
    Gram matrix B, this returns ``h - v^T B^-1 v`` and that residual divided by
    h.  A materially negative residual or singular basis aborts the screen so
    callers can fall back to exact scheduling rather than manufacture novelty.
    """
    matrix = _as_square_float_matrix(gram)
    n = len(matrix)
    basis_count = int(basis_count)
    if basis_count < 0 or basis_count > n:
        raise ValueError("basis_count is outside the height Gram matrix")

    B = [row[:basis_count] for row in matrix[:basis_count]]
    L = _cholesky(B) if basis_count else []
    out = []
    for idx in range(basis_count, n):
        height = matrix[idx][idx]
        if height < 0 and abs(height) > 1e-12:
            raise ValueError("candidate canonical height is materially negative")
        if height <= 0:
            out.append({
                "height": height,
                "projected_height": 0.0,
                "residual": 0.0,
                "relative_residual": 0.0,
            })
            continue

        cross = [matrix[i][idx] for i in range(basis_count)]
        coeffs = _solve_cholesky(L, cross) if basis_count else []
        projected = sum(v * c for v, c in zip(cross, coeffs))
        residual = height - projected
        scale = max(1.0, abs(height), abs(projected))
        if residual < -1e-9 * scale:
            raise ValueError("projection residual is materially negative")
        residual = max(0.0, residual)
        out.append({
            "height": height,
            "projected_height": projected,
            "residual": residual,
            "relative_residual": residual / height,
        })
    return out


def rank_novelty(records):
    """Sort screened records from largest to smallest relative residual."""
    def score(record):
        rel = record.get("relative_residual")
        residual = record.get("residual")
        return (
            float("-inf") if rel is None else float(rel),
            float("-inf") if residual is None else float(residual),
        )

    return sorted(records, key=score, reverse=True)
