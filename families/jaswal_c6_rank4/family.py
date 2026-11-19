"""The rational C6 family in Jaswal (2026), Theorem 1.1."""

from sage.all import EllipticCurve, GF, QQ


def name():
    return "Jaswal C6 generic rank 4"


def parameter_c(t):
    t2 = t * t
    t4 = t2 * t2
    t8 = t4 * t4
    numerator = 8 * t2 * (t2 - 1)**2 * (t4 - 8*t2 - 1) * (t4 + 8*t2 - 1)
    denominator = (t8 + 62*t4 + 1) * (t8 + 24*t2*t4 + 14*t4 + 24*t2 + 1)
    if denominator == 0:
        return None
    return numerator / denominator


def _curve(t):
    c = parameter_c(t)
    if c is None or c == 0 or c == -1 or 9*c + 1 == 0:
        return None
    return EllipticCurve(t.parent(), [0, 1 + 6*c - 3*c*c, 0, -16*c**3, 0])


def curve(t):
    return _curve(QQ(t))


def curve_mod_p(r, p):
    return _curve(GF(p)(r))


def torsion_point(t):
    t = QQ(t)
    c = parameter_c(t)
    E = _curve(t)
    return None if E is None else E(-4*c, 4*c*(1+c))
