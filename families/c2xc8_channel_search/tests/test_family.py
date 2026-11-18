from sage.all import GF, QQ

from family import canonical_parameter, curve, curve_mod_p, parameter_data


def test_published_control_and_torsion():
    E = curve(QQ(4))
    assert E.a_invariants() == (0, 54721, 0, 207360000, 0)
    assert tuple(E.torsion_subgroup().invariants()) == (2, 8)
    P, Q, T = E(800, 448800), E(96000, 37536000), E(-50625, 0)
    assert 8*Q == E(0)
    assert 4*Q == E(0, 0)
    assert 2*T == E(0)
    assert all(T != n*Q for n in range(8))
    assert 16*P != E(0)
    A, B = 50625, 4096
    assert E.discriminant() == 16*A*A*B*B*(A-B)**2


def test_parameter_boundaries_and_same_model_symmetries():
    assert all(curve(t) is None for t in (0, 1, -1))
    assert parameter_data("1/0") is None
    assert curve(4).a_invariants() == curve(-4).a_invariants()
    assert curve(4).a_invariants() == curve(QQ(1)/4).a_invariants()
    assert canonical_parameter(4) == canonical_parameter(-4) == canonical_parameter(QQ(1)/4)


def test_parameter_symmetry_also_collapses_coefficient_swap_orbit():
    parameters = [QQ(29)/5, QQ(5)/29, QQ(17)/12, QQ(12)/17]
    assert {canonical_parameter(t) for t in parameters} == {(5, 29)}
    reference = curve(QQ(29)/5)
    assert all(reference.is_isomorphic(curve(t)) for t in parameters)


def test_finite_field_reduction_uses_integral_model():
    E = curve(4)
    for p in (7, 11, 13, 17, 19, 23, 29):
        mod = curve_mod_p(4, p)
        if E.discriminant() % p:
            assert mod is not None
            assert mod.a_invariants() == tuple(GF(p)(a) for a in E.a_invariants())
        else:
            assert mod is None
