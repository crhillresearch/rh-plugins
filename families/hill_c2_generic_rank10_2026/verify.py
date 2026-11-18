#!/usr/bin/env sage -python
"""Standalone exact replay of the C2 paired-cover rank-11 family packet."""
import json
from math import gcd
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, ZZ, lcm, matrix, sage_eval

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'


def read(name):
    return json.loads((DATA / name).read_text())


def poly(R, value):
    if isinstance(value, list):
        return R([QQ(c) for c in value])
    return R(str(value).replace('^', '**'))


def make_short_model(doc, section_key, variable='U'):
    R = PolynomialRing(QQ, variable)
    K = R.fraction_field()
    A = R([QQ(c) for c in doc['jacobian_model']['a4_low_to_high']])
    B = R([QQ(c) for c in doc['jacobian_model']['a6_low_to_high']])
    E = EllipticCurve(K, [0, 0, 0, K(A), K(B)])
    rows = doc[section_key]
    points = []
    for row in rows:
        x = K(poly(R, row['x_numerator'])) / K(poly(R, row['x_denominator']))
        y = K(poly(R, row['y_numerator'])) / K(poly(R, row['y_denominator']))
        points.append(E(x, y))
    return R, K, E, points


def compose(value, argument):
    value = value
    return value.numerator()(argument) / value.denominator()(argument)


def i2_factors(R, E):
    delta, c4 = R(E.discriminant()), R(E.c4())
    assert delta.degree() > 0
    i2 = []
    for f, exponent in delta.factor():
        exponent = int(exponent)
        assert c4.valuation(f) == 0, f'c4 not a unit at {f}'
        assert exponent in (1, 2), f'unsupported fiber multiplicity {exponent}'
        if exponent == 2:
            i2.append(f)
    return delta, i2


def corrected_height(P, R, K, i2, node_x, chi):
    if not P:
        return QQ(0)
    x, y = K(P[0]), K(P[1])
    height = QQ(max(x.numerator().degree(), x.denominator().degree() + 2 * chi))
    for f in i2:
        xn = R((x - node_x).numerator())
        xd = R((x - node_x).denominator())
        yn, yd = R(y.numerator()), R(y.denominator())
        if xd.gcd(f).degree() or yd.gcd(f).degree():
            continue
        if xn % f == 0 and yn % f == 0:
            height -= QQ(f.degree()) / 2
    return height


def gram_of(points, R, K, i2, node_x, chi):
    heights = [corrected_height(P, R, K, i2, node_x, chi) for P in points]
    H = matrix(QQ, len(points))
    for i, P in enumerate(points):
        H[i, i] = heights[i]
        for j in range(i):
            H[i, j] = H[j, i] = (
                corrected_height(P + points[j], R, K, i2, node_x, chi)
                - heights[i] - heights[j]
            ) / 2
    return H


def main():
    family = read('source-family-u11_5.json')
    parent = read('parent-rank9.json')
    portfolio = read('quadratic-cover-portfolio.json')
    base = read('paired-cover-base.json')
    rank11 = read('rank11-family-certificate.json')

    # The nine common sections are independently recomputed on the parent.
    PR, PK, PE, parent_points = make_short_model(parent, 'neighbor_sections')
    assert len(parent_points) == 9
    u = PK.gen()
    a2 = sage_eval(str(family['a_invariants'][1]), locals={'t': u})
    parent_delta, parent_i2 = i2_factors(PR, PE)
    assert parent_delta.degree() == 24
    assert sum(f.degree() for f in parent_i2) == 8
    assert sum(f.degree() for f, e in parent_delta.factor() if int(e) == 1) == 8
    parent_H = gram_of(parent_points, PR, PK, parent_i2, PK(a2) / 3, 2)
    stored_parent_H = matrix(QQ, parent['exact_generic_section_basis']['height_matrix'])
    assert parent_H == stored_parent_H
    assert parent_H.is_positive_definite() and parent_H.det() == QQ(115) / 16
    print('Parent: 9 independent sections; corrected Gram determinant 115/16')

    # The two distinct square classes define the biquadratic genus-one base.
    T = PolynomialRing(QQ, 't')
    t = T.gen()
    cover_rows = portfolio['sections']
    indices = [int(v) for v in base['cover_indices']]
    assert indices == [10, 13]
    branches = [T([QQ(v) for v in cover_rows[i - 1]['cover_coefficients']]) for i in indices]
    assert all(q.degree() == 2 and q.gcd(q.derivative()).degree() == 0 for q in branches)
    assert branches[0].gcd(branches[1]).degree() == 0
    N, D, W = [T([QQ(v) for v in base[k]]) for k in
               ('parent_numerator', 'parent_denominator', 'first_root_numerator')]
    quartic = T([QQ(v) for v in base['quartic']])
    assert N.degree() == D.degree() == W.degree() == 2 and N.gcd(D).degree() == 0
    q1, q2 = branches
    assert q1[2] * N**2 + q1[1] * N * D + q1[0] * D**2 == W**2
    assert q2[2] * N**2 + q2[1] * N * D + q2[0] * D**2 == quartic
    assert quartic.degree() == 4 and quartic.gcd(quartic.derivative()).degree() == 0
    assert quartic[0] > 0 and quartic[0].is_square()

    e, d, c, b, a = quartic[0].sqrt(), quartic[1], quartic[2], quartic[3], quartic[4]
    aux_formula = [0, c, 0, b*d - 4*a*e**2, e**2*b**2 + a*d**2 - 4*a*c*e**2]
    aux = EllipticCurve(QQ, [QQ(v) for v in base['auxiliary_a_invariants']])
    assert list(map(QQ, aux.a_invariants())) == list(map(QQ, aux_formula))
    sR = PolynomialRing(QQ, 's')
    s = sR.gen()
    sK = sR.fraction_field()
    wR = PolynomialRing(sK, 'w')
    w = wR.gen()
    F = wR(sK(T(quartic)))
    X = (2*e*(w + e) + d*s) / s**2
    Y = ((X**2 - 4*e**2*a)*s - (X*d + 2*e**2*b)) / (2*e)
    relation = Y**2 - (X**3 + c*X**2 + (b*d - 4*a*e**2)*X
                      + e**2*b**2 + a*d**2 - 4*a*c*e**2)
    assert relation % (w**2 - F) == 0

    P = aux(*[QQ(v) for v in base['auxiliary_point']])
    reduction_sizes = {}
    for prime, claimed in base['reduction_orders']:
        prime, claimed = ZZ(prime), ZZ(claimed)
        assert prime.is_prime() and prime >= 5
        assert aux.discriminant().numerator() % prime != 0
        actual = ZZ(aux.change_ring(GF(prime)).cardinality())
        assert actual == claimed
        reduction_sizes[int(prime)] = actual
    possible_ell = set()
    for size in reduction_sizes.values():
        possible_ell.update(map(int, size.prime_divisors()))
    torsion_multiple = ZZ(1)
    for ell in possible_ell:
        vals = [ZZ(size).valuation(ell) for p, size in reduction_sizes.items() if p != ell]
        if vals:
            torsion_multiple *= ell ** min(vals)
    assert torsion_multiple == 2 and torsion_multiple * P != aux(0)
    print('Base: exact quartic/Jacobian map; rational point is nontorsion')

    # Replay both full correction-aware ten-by-ten Shioda matrices.
    receipts = []
    for index in indices:
        model = read(f'cover-{index}/model.json')
        receipt = read(f'cover-{index}/shioda-certificate.json')
        assert int(model['source_cover_index']) == index
        assert receipt['status'] == 'certified_exact_rank10_on_quadratic_cover'
        R, K, E, points = make_short_model(model, 'sections')
        assert len(points) == 10
        n = R([QQ(v) for v in model['quadratic_basechange']['parameter_numerator']])
        den = R([QQ(v) for v in model['quadratic_basechange']['parameter_denominator']])
        tt = K(n) / K(den)
        assert R(E.a4()) == R(den**8 * compose(PK(PE.a4()), tt))
        assert R(E.a6()) == R(den**12 * compose(PK(PE.a6()), tt))
        for old, pulled in zip(parent_points, points[:9]):
            assert pulled[0] == den**4 * compose(old[0], tt)
            assert pulled[1] == den**6 * compose(old[1], tt)

        delta, i2 = i2_factors(R, E)
        assert delta.degree() == 48
        node_x = K(den)**4 * (K(a2)(tt) / 3)
        H = gram_of(points, R, K, i2, node_x, 4)
        stored = matrix(QQ, receipt['gram'])
        assert H == stored == matrix(QQ, model['exact_generic_section_basis']['height_matrix'])
        assert H.is_positive_definite() and H.det() == 11040
        assert H[:9, :9] == 2 * parent_H
        residual = H[9, 9] - (H[9, :9] * H[:9, :9].inverse() * H[:9, 9])[0, 0]
        assert residual == QQ(3) == QQ(receipt['new_section_orthogonal_residual_height'])

        z = K.gen()
        ubar = (n[0] - tt*den[0]) / ((n[2] - tt*den[2]) * z)
        assert n(ubar) / den(ubar) == tt
        scale = K(den) / K(den)(ubar)

        def conjugate(Q):
            def sub(value):
                return value.numerator()(ubar) / value.denominator()(ubar)
            return E(sub(Q[0]) * scale**4, sub(Q[1]) * scale**6)

        assert all(conjugate(Q) == Q for Q in points[:9])
        anti = points[9] - conjugate(points[9])
        assert anti and corrected_height(anti, R, K, i2, node_x, 4) == 12
        receipts.append({'cover': index, 'determinant': str(H.det()), 'residual': str(residual)})
        print(f'Cover {index}: recomputed rank-10 Gram; determinant 11040; anti-invariant height 12')

    # Exact C2 specialization and non-isotriviality imply the family claims.
    seed = QQ(-13) / 30
    tR = PolynomialRing(QQ, 't')
    tt = tR.fraction_field().gen()
    ainvs = [tR.fraction_field()(sage_eval(str(v), locals={'t': tt})) for v in family['a_invariants']]
    Efamily = EllipticCurve(tR.fraction_field(), ainvs)
    assert Efamily.j_invariant().derivative() != 0
    visible_2_torsion = Efamily(0, 0)
    assert visible_2_torsion and 2 * visible_2_torsion == Efamily(0)
    specialized_ainvs = [QQ(sage_eval(str(v), locals={'t': seed})) for v in family['a_invariants']]
    specialized = EllipticCurve(QQ, specialized_ainvs)
    assert specialized.discriminant() != 0
    torsion = [int(v) for v in specialized.torsion_subgroup().invariants()]
    assert torsion == [2]

    assert rank11['status'] == 'certified_generic_rank_lower_bound_over_genus_one_base'
    assert rank11['rank_lower_bound'] == 11
    assert rank11['torsion_subgroup'] == 'C2'
    assert rank11['parameter_base_genus'] == 1 and rank11['nonisotrivial']
    assert rank11['infinitely_many_rank11_specializations']
    print('Torsion: exact C2 at smooth split fiber; j is nonconstant')
    print('CERTIFIED: infinitely many rational C2-torsion fibers have rank at least 11')


if __name__ == '__main__':
    main()
