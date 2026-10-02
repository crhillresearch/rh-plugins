"""Small pure helpers retained by the standalone Mestre family plugin.

These functions were formerly imported from two generic experimental helper
modules removed from Rank Hunter core in older releases.  Only the five functions
actually required by the Mestre search workers are kept here.  They perform
parsing, deterministic point selection, and *numerical* height-lattice
screening; none is a rank certificate.
"""
from __future__ import annotations

import math
from fractions import Fraction


def parse_height_stages(text: str | list[int] | tuple[int, ...]) -> list[int]:
    if isinstance(text, (list, tuple)):
        values = [int(x) for x in text]
    else:
        values = [int(x.strip()) for x in str(text).split(",") if x.strip()]
    if not values or any(x <= 0 for x in values):
        raise ValueError("ratpoints height stages must be positive integers")
    return sorted(set(values))


def canonical_affine_key(x, y) -> tuple[str, str]:
    """Identify a finite point up to P -> -P on a short Weierstrass model."""
    qx = x if isinstance(x, Fraction) else Fraction(str(x))
    qy = y if isinstance(y, Fraction) else Fraction(str(y))
    if qy < 0:
        qy = -qy
    return str(qx), str(qy)


def _height_key(point) -> tuple[int, int, int, int, int, int]:
    x, y = point[0], point[1]
    qx = x if isinstance(x, Fraction) else Fraction(str(x))
    qy = y if isinstance(y, Fraction) else Fraction(str(y))
    hx = max(abs(qx.numerator), qx.denominator)
    hy = max(abs(qy.numerator), qy.denominator)
    return (max(hx, hy), hx, hy, qx.denominator, qy.denominator, abs(qx.numerator))


def _spread_indices(count: int, limit: int) -> list[int]:
    count, limit = max(0, int(count)), max(0, int(limit))
    if count == 0 or limit == 0:
        return []
    if limit >= count:
        return list(range(count))
    if limit == 1:
        return [0]
    chosen, seen = [], set()
    for k in range(limit):
        idx = int(round(k * (count - 1) / (limit - 1)))
        if idx not in seen:
            chosen.append(idx); seen.add(idx)
    if len(chosen) < limit:
        for idx in range(count):
            if idx not in seen:
                chosen.append(idx); seen.add(idx)
                if len(chosen) >= limit:
                    break
    return sorted(chosen)


def spread_points(points, limit: int):
    ordered = sorted(points, key=_height_key)
    return [ordered[i] for i in _spread_indices(len(ordered), limit)]


def _cholesky_solve(matrix: list[list[float]], rhs: list[float], *, rel_tol: float = 1e-14) -> list[float]:
    n = len(matrix)
    if n == 0:
        return []
    if len(rhs) != n or any(len(row) != n for row in matrix):
        raise ValueError("basis Gram matrix dimensions do not match")
    scale = max(1.0, max(abs(float(matrix[i][i])) for i in range(n)))
    floor = float(rel_tol) * scale
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        pivot = float(matrix[i][i]) - sum(L[i][k] * L[i][k] for k in range(i))
        if not math.isfinite(pivot) or pivot <= floor:
            raise ValueError("basis Gram matrix is not numerically positive definite")
        L[i][i] = math.sqrt(pivot)
        for j in range(i + 1, n):
            numer = float(matrix[j][i]) - sum(L[j][k] * L[i][k] for k in range(i))
            L[j][i] = numer / L[i][i]
    y = [0.0] * n
    for i in range(n):
        y[i] = (float(rhs[i]) - sum(L[i][k] * y[k] for k in range(i))) / L[i][i]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(L[k][i] * x[k] for k in range(i + 1, n))) / L[i][i]
    return x


def projection_residuals(gram, basis_size: int) -> list[dict]:
    """Schur-complement residuals used only as a numerical novelty screen."""
    M = [[float(v) for v in row] for row in gram]
    n = len(M)
    if any(len(row) != n for row in M):
        raise ValueError("Gram matrix must be square")
    r = int(basis_size)
    if r < 0 or r > n:
        raise ValueError("invalid basis size")
    if r == 0:
        return [{"candidate_offset": j, "residual": float(M[j][j]),
                 "relative_residual": 1.0 if float(M[j][j]) > 0 else 0.0,
                 "candidate_height": float(M[j][j])} for j in range(n)]
    G = [[M[i][j] for j in range(r)] for i in range(r)]
    out = []
    for j in range(r, n):
        b = [M[i][j] for i in range(r)]
        x = _cholesky_solve(G, b)
        h = float(M[j][j])
        residual = h - sum(bi * xi for bi, xi in zip(b, x))
        out.append({"candidate_offset": j-r, "residual": residual,
                    "relative_residual": residual / max(abs(h), 1e-30),
                    "candidate_height": h})
    return out


def rank_novelty(records: list[dict], *, retain: int | None = None) -> list[dict]:
    ordered = sorted(records, key=lambda rec: (
        -float(rec.get("relative_residual", float("-inf"))),
        -float(rec.get("residual", float("-inf"))),
        str(rec.get("x", "")), str(rec.get("y", ""))))
    return ordered if retain is None else ordered[:max(0, int(retain))]
