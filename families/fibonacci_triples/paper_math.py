"""Exact paper formulas independent of Sage.

The arithmetic functions use only +, -, *, / and therefore work with
``fractions.Fraction`` as well as Sage rational/function/finite fields.

Scientific claim boundary:
- ``generic_rank`` values come from Theorem 5.1 of Dujella's paper.
- ``minimalist_expected_rank`` is a parity/minimalist heuristic, not a proof.
"""
from __future__ import annotations

from fractions import Fraction


def _half(x):
    return x / 2


def odd_parameters(t):
    """Return (f, ell, u, v, ell1, ell2, a, b, c) for E_-.

    Implements equations (14) and the definitions immediately following (15).
    The caller is responsible for choosing a field in which ``t^2 - 5`` is
    nonzero.
    """
    d = t * t - 5
    f = (t * t - 2 * t + 5) / d
    ell = -(t * t - 10 * t + 5) / d
    u = _half(ell + f)
    v = _half(ell + 3 * f)
    ell1 = _half(ell + 5 * f)
    ell2 = _half(3 * ell + 5 * f)
    a = f * ell
    b = u * ell1
    c = v * ell2
    return f, ell, u, v, ell1, ell2, a, b, c


def even_parameters(t):
    """Return (f, ell, u, v, ell1, ell2, a, b, c) for E_+."""
    d = t * t - 5
    f = -4 * t / d
    ell = -2 * (t * t + 5) / d
    u = _half(ell + f)
    v = _half(ell + 3 * f)
    ell1 = _half(ell + 5 * f)
    ell2 = _half(3 * ell + 5 * f)
    a = f * ell
    b = u * ell1
    c = v * ell2
    return f, ell, u, v, ell1, ell2, a, b, c


def transformed_a_invariants(a, b, c):
    """a-invariants after X=abc*x, Y=abc*y.

    Y^2=(X+bc)(X+ac)(X+ab).
    """
    abc = a * b * c
    return (0, a * b + a * c + b * c, 0, abc * (a + b + c), abc * abc)


def odd_section_coordinates(t):
    """Return transformed Weierstrass coordinates for the paper's P and Q."""
    f, ell, u, v, ell1, ell2, a, b, c = odd_parameters(t)
    abc = a * b * c
    P = (0, abc)
    # Q is equation (16) in native coordinates, simplified after X=abc*x,
    # Y=abc*y.
    Q = (
        -f * ell1 * ell2 * (u - f),
        f * ell1 * ell2 * (f * f + u * u),
    )
    return P, Q


def even_section_coordinates(t):
    """Return the transformed standard section P for E_+."""
    *_, a, b, c = even_parameters(t)
    return ((0, a * b * c),)


def fibonacci(n):
    """Exact F_n for n >= 0 using fast doubling."""
    n = int(n)
    if n < 0:
        raise ValueError("n must be nonnegative")

    def fd(m):
        if m == 0:
            return 0, 1
        a, b = fd(m // 2)
        c = a * (2 * b - a)
        d = a * a + b * b
        return (d, c + d) if m & 1 else (c, d)

    return fd(n)[0]


def lucas(n):
    """Exact L_n for n >= 0."""
    n = int(n)
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n == 0:
        return 2
    return fibonacci(n - 1) + fibonacci(n + 1)


def fibonacci_triple(k):
    """Return (F_{2k}, F_{2k+2}, F_{2k+4}) for positive integer k."""
    k = int(k)
    if k < 1:
        raise ValueError("k must be positive")
    return fibonacci(2 * k), fibonacci(2 * k + 2), fibonacci(2 * k + 4)


def family_parameter_for_index(k):
    """Return the paper parameter T for a Fibonacci specialization.

    For odd k >= 3, inversion of (14) gives T=(L_k-1)/(F_k-1).
    For even k, inversion of (15) gives T=5F_k/(L_k+2).
    The k=1 point is the finite-parameter exception (Q_1=P_1) and is not
    represented by the odd affine T chart used by this plugin.
    """
    k = int(k)
    if k < 1:
        raise ValueError("k must be positive")
    F = fibonacci(k)
    L = lucas(k)
    if k % 2:
        if k == 1:
            raise ValueError("k=1 is not represented by the odd affine T chart")
        return Fraction(L - 1, F - 1)
    return Fraction(5 * F, L + 2)


def native_odd_q(k):
    """Return Q_k in the original x,y model for odd positive k."""
    k = int(k)
    if k < 1 or k % 2 == 0:
        raise ValueError("Q_k formula is for odd positive k")
    D = lucas(k) * fibonacci(k + 1) * fibonacci(k + 2)
    return Fraction(-fibonacci(k - 1), D), Fraction(fibonacci(2 * k + 1), D)


def forced_rank_baseline(k):
    """Published specialization lower-bound baseline relevant to the heuristic.

    For odd k >= 3, P_k and Q_k are proved independent (rank >= 2).
    For even k, only the standard forced point is used here (rank >= 1).
    k=1 is exceptional because Q_1=P_1.
    """
    k = int(k)
    if k < 1:
        raise ValueError("k must be positive")
    return 2 if (k % 2 and k >= 3) else 1


def minimalist_expected_rank(k, root_number):
    """Parity/minimalist expected rank for a Fibonacci index.

    ``root_number`` must be +1 or -1.  The return value is heuristic only:
    choose the smallest rank at least the forced baseline with parity predicted
    by W(E)=(-1)^rank.
    """
    w = int(root_number)
    if w not in (-1, 1):
        raise ValueError("root_number must be +1 or -1")
    r = forced_rank_baseline(k)
    want_odd = (w == -1)
    if bool(r % 2) != want_odd:
        r += 1
    return r


def rank_distribution_heuristic():
    """Conjecture 6.1 densities, represented exactly."""
    return {1: Fraction(1, 4), 2: Fraction(1, 2), 3: Fraction(1, 4), "rank>=4": Fraction(0, 1)}
