"""Exact published MW17 family for Elkies' X1092 fibration.

Data transcribed from arXiv:2608.25406v1, Sections 2.1--2.2, matching the
uploaded Rank32 x1092_sections.py source.  The 17 specialized points are
returned in the preserved basis order S1..S17.
"""
from __future__ import annotations

from fractions import Fraction

from sage.all import QQ, GF, EllipticCurve, PolynomialRing, matrix

GENERIC_RANK = 17
generic_rank = GENERIC_RANK
LEADING_Y_SIGNS = "-+-+++++-+-+++-++"

PUBLISHED_GENERIC_GRAM = (
    (4,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,1),
    (-2,4,2,1,0,1,0,1,1,1,1,2,1,1,1,1,1),
    (-2,2,4,2,1,0,1,2,1,1,1,0,1,1,2,1,0),
    (-2,1,2,4,1,0,1,1,2,1,1,1,0,1,0,1,0),
    (-2,0,1,1,4,2,0,1,1,0,1,1,1,2,1,0,-1),
    (-2,1,0,0,2,4,1,0,0,1,2,1,1,1,1,0,-1),
    (-2,0,1,1,0,1,4,0,0,1,1,0,1,1,2,2,-2),
    (-2,1,2,1,1,0,0,4,1,2,1,0,1,1,1,1,0),
    (-2,1,1,2,1,0,0,1,4,2,2,1,2,2,1,1,-1),
    (-2,1,1,1,0,1,1,2,2,4,2,0,2,1,2,1,-1),
    (-2,1,1,1,1,2,1,1,2,2,4,0,1,2,2,1,-2),
    (-2,2,0,1,1,1,0,0,1,0,0,4,0,1,0,1,1),
    (-2,1,1,0,1,1,1,1,2,2,1,0,4,2,2,1,-2),
    (-2,1,1,1,2,1,1,1,2,1,2,1,2,4,2,1,-2),
    (-2,1,2,0,1,1,2,1,1,2,2,0,2,2,4,1,-2),
    (-2,1,1,1,0,0,2,1,1,1,1,1,1,1,1,4,0),
    (1,1,0,0,-1,-1,-2,0,-1,-1,-2,1,-2,-2,-2,0,4),
)

S = (
    4201305425690184127251888481,
    17860826619093915900857289304,
    28607402618712438778345257832,
    21430123310022469548285709072,
    8789387383568632081365832240,
    2020678721371875903158954848,
    234256046667228607566274912,
    10476571005172375234427296,
    307516108335972163537936,
)

T = (
    2193201312876924214657300134273061462776968,
    13865015501478235534002649882546248548532768,
    36435013603665838306995466090052055171475872,
    52862444598312784274784438443066814490530880,
    47243082583908684509409509915652973906060800,
    26905633537996991160744810870319331164617600,
    9904246958414858348647761354992989326760320,
    2373760737463050257069464720014664373086080,
    372202978476351718721663756748866085220800,
    38126035250980128714796491999580538771200,
    2392486076703808362288120169049836903680,
    67802587761728815952013525763236564480,
    1050290276365892761266194577222156800,
)

X1 = (304456582100883,448019664127620,84146613883956,-6900780974412,419884536396)
Y1 = (
    2913630401455186533120,
    3523393851784245137088,
    -3519107150812739581680,
    -4035207954948742785564,
    -1140847719698231045748,
    -102352278854532258864,
    -1917605876395727232,
)

M = (
    (9306987,17472654,3609606),
    (10995509,-47135036,-13842426),
    (25228749,34503044,5619654),
    (25181877,16309708,2903654),
    (1645077,-7417332,-1674426),
    (35277,Fraction(-6644079,2),Fraction(-2879877,2)),
    (-401684283,-74149065,-1293435),
    (-102088725,56959398,598182),
    (-58915563,-29297801,3845621),
    (18889077,21342168,Fraction(3959553,2)),
    (29039811,2320578,-2966262),
    (-59230479,907317,2648379),
    (38513982,20056077,1508406),
    (106182447,32579784,-1022424),
    (-3300003,-12262536,-4556214),
)

X = (
    (136981770876723,451794461129916,228946163155128,32982109084392,960407733324),
    (-329325794912045,-1605097821400112,1886874275645632,1333867432517100,191092188813708),
    (205182206512275,489728900722308,191145949680312,20106018946320,881331598668),
    (124968924115923,70169296825056,119727776998960,60084894852268,7087168886668),
    (-379495133581677,-794565531069024,-436645278959760,-75993994150932,-2654105330292),
    (-362275017421677,-839785632779964,-435348555495516,-76265967628812,-2842297467828),
    (320073994727283,464786649518334,63026792718435,-25598671575906,-2947994548863),
    (9732633560757363,-12715093268802228,2834155382615496,54450640822344,-2414976971316),
    (521473683384723,666777676835166,-242466751598877,-250429886278338,13412195434209),
    (-125053466701677,-55497536934924,271192708423620,62514191744628,353434406988),
    (345607319019603,-653155402766412,-486949775116428,-83483171473260,-1586365228500),
    (2685202943830203,-1492345666793982,-764745203764737,-29562185743194,5724934740993),
    (964931580370398,694007861500356,164233784236041,18957579322812,2426651051916),
    (260813404752123,413697107315976,153585168336648,27061905787332,3734241561804),
    (-287286844790877,-678508004328024,-354534107851872,-57890934328188,-798764561556),
    (408936541867923,494998206601236,206429765168484,25332675721548,2607059076492),
)

M17 = (-11613683,3253646,-183750)


def name():
    return "Elkies X1092 published rank-17 fibration"


def _eval(coeffs, t):
    out = t.parent()(0) if hasattr(t, "parent") else QQ(0)
    for coefficient in reversed(coeffs):
        out = out*t + t.parent()(coefficient) if hasattr(t, "parent") else out*t + QQ(coefficient)
    return out


def _coeff(value, ring):
    if isinstance(value, Fraction):
        return ring(value.numerator) / ring(value.denominator)
    return ring(value)


def _eval_ring(coeffs, t, ring):
    out = ring(0)
    for coefficient in reversed(coeffs):
        out = out*t + _coeff(coefficient, ring)
    return out


def _curve_coefficients(t, ring):
    s = _eval_ring(S, t, ring)
    tt = _eval_ring(T, t, ring)
    return [ring(0), ring(0), ring(0), -ring(27)*s, ring(27)*tt/ring(4)]


def curve(t):
    try:
        tq = QQ(t)
        E = EllipticCurve(QQ, _curve_coefficients(tq, QQ))
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(r, p):
    try:
        F = GF(int(p))
        if F.characteristic() in (2,):
            return None
        tr = F(int(r))
        E = EllipticCurve(F, _curve_coefficients(tr, F))
        return None if E.discriminant() == 0 else E
    except (ArithmeticError, ValueError, ZeroDivisionError, TypeError):
        return None


def _section_xy(t, ring):
    x1 = _eval_ring(X1, t, ring)
    y1 = _eval_ring(Y1, t, ring)
    out = [(x1, y1)]
    for slope_coeffs, x_coeffs in zip(M, X[:15]):
        slope = _eval_ring(slope_coeffs, t, ring)
        xx = _eval_ring(x_coeffs, t, ring)
        yy = y1 + slope*(xx-x1)
        out.append((xx, yy))
    x17 = _eval_ring(X[15], t, ring)
    x7, y7 = out[6]
    y17 = y7 + _eval_ring(M17, t, ring)*(x17-x7)
    out.append((x17, y17))
    return tuple(out)



def nagao_score_table(p):
    """Return log(#E_t(F_p)/p) for every t in F_p using vectorized point counts.

    This avoids constructing p separate Sage elliptic-curve objects for each
    prime during candidate screening.  The family is short Weierstrass:
        y^2 = x^3 + A(t) x + B(t)
    with A=-27*S and B=27*T/4.
    """
    import math
    import numpy as np

    p = int(p)
    if p <= 2:
        return [None] * p

    residues = np.arange(p, dtype=np.int64)

    def eval_poly_mod(coeffs):
        out = np.zeros(p, dtype=np.int64)
        for coefficient in reversed(coeffs):
            c = coefficient
            if isinstance(c, Fraction):
                den = pow(int(c.denominator) % p, -1, p)
                cmod = (int(c.numerator) % p) * den % p
            else:
                cmod = int(c) % p
            out = (out * residues + cmod) % p
        return out

    sval = eval_poly_mod(S)
    tval = eval_poly_mod(T)
    A = (-27 * sval) % p
    inv4 = pow(4, -1, p)
    B = (27 * inv4 * tval) % p

    # Singular short-Weierstrass fibers satisfy 4*A^3 + 27*B^2 == 0 mod p.
    singular = (4 * (A*A % p) * A + 27 * (B*B % p)) % p == 0

    # Quadratic-character lookup on F_p.
    chi = np.full(p, -1, dtype=np.int16)
    sq = (residues * residues) % p
    chi[sq] = 1
    chi[0] = 0

    counts = np.ones(p, dtype=np.int64)  # point at infinity
    # Stream over x to keep memory O(p), while vectorizing over all t residues.
    for x in range(p):
        rhs = (pow(x, 3, p) + (A * x) + B) % p
        counts += 1 + chi[rhs]

    out = []
    for r in range(p):
        if bool(singular[r]):
            out.append(None)
        else:
            out.append(math.log(int(counts[r]) / p))
    return out

def generic_section_points(t):
    E = curve(t)
    if E is None:
        return []
    tq = QQ(t)
    return [E(x, y) for x, y in _section_xy(tq, QQ)]


def generic_section_metadata(t):
    tq = QQ(t)
    coords = _section_xy(tq, QQ)
    out = []
    for index, (x, y) in enumerate(coords, 1):
        vector = [0]*17
        vector[index-1] = 1
        out.append({
            "basis_label": f"S{index}",
            "coefficient_vector": vector,
            "search_label": f"1*S{index}",
            "trace_coordinates": [str(x), str(y)],
            "leading_y_sign": LEADING_Y_SIGNS[index-1],
            "generic_basis": "X1092 published MW17",
        })
    return out


def validate_symbolically():
    R = PolynomialRing(QQ, "t")
    K = R.fraction_field()
    t = K(R.gen())
    E = EllipticCurve(K, _curve_coefficients(t, K))
    coords = _section_xy(t, K)
    points = [E(x, y) for x, y in coords]
    return {
        "name": name(),
        "generic_rank_declared": 17,
        "sections_verified_on_curve": len(points),
        "x_degrees": [x.numerator().degree() for x, _ in coords],
        "y_degrees": [y.numerator().degree() for _, y in coords],
    }


def _published_height_gram():
    """Recompute Elkies's height pairing from the exact bundled sections."""
    R = PolynomialRing(QQ, "t")
    K = R.fraction_field()
    t = K(R.gen())
    coords = _section_xy(t, K)
    xs = [R(x) for x, _ in coords]
    ys = [R(y) for _, y in coords]

    def pairing(i, j):
        if i == j:
            return QQ(4)
        dx = xs[i] - xs[j]
        dy = ys[i] - ys[j]
        finite = dx.gcd(dy).degree()
        infinity = min(4 - dx.degree(), 6 - dy.degree())
        return QQ(2 - (finite + infinity))

    return matrix(QQ, 17, 17, pairing)


def validate_generic_rank_claim():
    """Verify the published MW17 lower bound required by Rank Hunter core."""
    symbolic = validate_symbolically()
    if int(symbolic["sections_verified_on_curve"]) != 17:
        raise ValueError("published MW17 claim requires all 17 exact sections")

    gram = _published_height_gram()
    expected = matrix(QQ, PUBLISHED_GENERIC_GRAM)
    if gram != expected:
        raise ValueError("recomputed height-pairing Gram matrix does not match Elkies")
    determinant = gram.det()
    if determinant != 948:
        raise ValueError(
            f"published MW17 height determinant mismatch: expected 948, got {determinant}"
        )

    return {
        "verified": True,
        "lower_bound": 17,
        "method": "17 exact generic sections + exact recomputation of Elkies's published height-pairing Gram matrix",
        "certificate_version": "rank-hunter.elkies-x1092-mw17-generic-lower.v1",
        "details": {
            "arxiv": "2608.25406v1",
            "theorem_reference": "Theorem 4 and §2.2",
            "sections_verified_on_curve": 17,
            "height_gram_matches_published": True,
            "height_gram_determinant": str(determinant),
            "published_rank_is_maximal_for_elliptic_k3": True,
        },
    }
