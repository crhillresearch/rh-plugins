"""Naskręcki C2 × C8 family in a primitive integral Weierstrass model."""
from __future__ import annotations

from sage.all import EllipticCurve, GF, QQ, ZZ

parameter_symmetry = "canonical"  # Use this module's exact parameter-orbit reducer.


def name():
    return "C2 × C8 · Naskręcki channel family"


def parameter_data(t):
    """Return primitive (a,b,D,M,A,B); reject poles and singular fibers."""
    try:
        q = QQ(t)
        a, b = ZZ(q.numerator()), ZZ(q.denominator())
        if b <= 0 or a == 0 or a == b or a == -b:
            return None
        D, M = a*a - b*b, 2*a*b
        A, B = D**4, M**4
        if not D or not M or A == B:
            return None
        return a, b, D, M, A, B
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def canonical_parameter(t):
    """Collapse exact Q-isomorphism symmetries of the split C2 x C8 model.

    Besides sign and reciprocal symmetries, t -> (t+1)/(t-1) swaps the two
    fourth-power coefficients up to a common fourth-power scale. It therefore
    gives a Q-isomorphic elliptic curve, although the displayed models may
    differ.
    """
    data = parameter_data(t)
    if data is None:
        return None
    q = QQ(t)
    orbit_representatives = []
    for value in (q, (q + 1) / (q - 1)):
        a, b = ZZ(value.numerator()), ZZ(value.denominator())
        if b < 0:
            a, b = -a, -b
        orbit_representatives.append(min((abs(a), b), (b, abs(a))))
    return min(orbit_representatives)


def curve(t):
    data = parameter_data(t)
    if data is None:
        return None
    A, B = data[4:]
    try:
        E = EllipticCurve(QQ, [0, A+B, 0, A*B, 0])
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError):
        return None


def curve_mod_p(t, p):
    data = parameter_data(t)  # Normalize over Q before reducing coefficients.
    if data is None:
        return None
    try:
        prime = ZZ(p)
        if not prime.is_prime():
            return None
        K = GF(prime)
        A, B = K(data[4]), K(data[5])
        E = EllipticCurve(K, [0, A+B, 0, A*B, 0])
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None
