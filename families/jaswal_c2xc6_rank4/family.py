"""Jaswal C2 x C6 genus-one family, with m as an affine chart."""

from sage.all import EllipticCurve, GF, QQ


def name():
    return "Jaswal C2 x C6 genus-one rank 4"


def base_lift(m):
    g = 16*m**4 - 192*m**3 + 1456*m*m - 1920*m + 1600
    return g.sqrt() if g.is_square() else None


def _curve(m):
    if base_lift(m) is None or m*m == 10:
        return None
    s = (m*m - 16*m + 10)/(m*m - 10)
    if 3 - s*s == 0:
        return None
    v = 6/(3 - s*s)
    a = (v+1)**3 * (3*v-5)
    b = 32*(v-1)**3
    E = EllipticCurve(m.parent(), [0, -a-b, 0, a*b, 0])
    return E if E.discriminant() else None


def curve(t):
    return _curve(QQ(t))


def curve_mod_p(r, p):
    return _curve(GF(p)(r))
