from fractions import Fraction as Q

ROOTS = (0, 55, 314, 378, 1007, 1036)


def evaluate(coeffs, x):
    out = Q(0)
    for c in reversed(coeffs):
        out = out * x + c
    return out


def quartic_coefficients(u):
    s = 2 * Q(u)
    s2, s4, s6 = s*s, s**4, s**6
    return (
        s6 - 879500*s4 + 102302344648*s2 + 18103855887324900,
        30*(62*s4 - 21690305*s2 - 8594794400346),
        -(2*s4 - 1718550*s2 - 1195214262641),
        -30*(62*s2 + 68377393),
        s2 + 1149050,
    )


def g_coefficients(u):
    s = 2 * Q(u)
    s2, s4, s6 = s*s, s**4, s**6
    return (
        -s6 + 1165925*s4 - 128370083212*s2,
        -2790*s4 + 1034713080*s2 - 6810411651120,
        3*s4 - 3892050*s2 + 176868664084,
        5580*s2 - 1106081640,
        2726125 - 3*s2,
        -2790,
        1,
    )


def verify(u):
    u = Q(u)
    s = 2*u
    quartic = quartic_coefficients(u)
    g = g_coefficients(u)
    scale = 101232*u
    points = []
    for root in ROOTS:
        for sign in (-1, 1):
            x = Q(root) + sign*s
            y = evaluate(g, x) / scale
            assert y*y == evaluate(quartic, x)
            points.append((x, y))
    x = Q(1256, 5) - Q(17, 35)*s
    y = (936*s**3 - 254422*s**2 - 283436139*s + 34925066050) / Q(1225)
    assert y*y == evaluate(quartic, x)
    points.append((x, y))
    assert len(points) == 13
    assert len({p[0] for p in points}) == 13
    assert quartic == quartic_coefficients(-u)


def test_controls():
    for u in (Q(1), Q(7,3), Q(19754,39), Q(28917,20)):
        verify(u)


if __name__ == '__main__':
    test_controls()
    print('PASS Fermigier rank-12 formula regression')
