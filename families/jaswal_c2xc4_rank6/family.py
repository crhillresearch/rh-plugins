"""First Jaswal C2 x C4 genus-one family, using m as an affine chart."""

from sage.all import EllipticCurve, GF, QQ


def name():
    return "Jaswal C2 x C4 genus-one rank 6"


def base_lift(m):
    u2 = 5*(3*m*m + 242)
    v2 = 5*(2*m*m + 243)
    if not u2.is_square() or not v2.is_square():
        return None
    return u2.sqrt(), v2.sqrt()


def _curve(m):
    if base_lift(m) is None:
        return None
    a = 7*(m-99)*(m+1)*(m-11)*(m+9)
    b = -7*(m+99)*(m-1)*(m+11)*(m-9)
    if a*b*(a*a-b*b) == 0:
        return None
    return EllipticCurve(m.parent(), [0, a*a+b*b, 0, a*a*b*b, 0])


def curve(t):
    return _curve(QQ(t))


def curve_mod_p(r, p):
    return _curve(GF(p)(r))
