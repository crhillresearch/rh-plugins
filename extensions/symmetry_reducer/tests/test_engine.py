from pathlib import Path
import sys
HERE=Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from engine import (
    apply_pgl2,audit_weierstrass_2torsion,chart_audit_from_payload,
    compose,group_closure,matrix_signature,recover_pgl2_from_samples,
    reduce_chart_orbits,weierstrass_2torsion_action
)
from fractions import Fraction


def test_full_2torsion_x3_minus_x_gives_klein_four():
    r=audit_weierstrass_2torsion({"a2":0,"a4":-1,"a6":0})
    assert r["rational_2torsion_x"] == ["-1","0","1"]
    assert r["generated_action_group_order"] == 4


def test_torsion_action_formula_r0_is_minus_reciprocal():
    g=weierstrass_2torsion_action(0,0,-1)
    assert g == (0,1,-1,0) or g == (0,-1,1,0)
    assert apply_pgl2(g,Fraction(2)) == Fraction(-1,2)
    assert matrix_signature(compose(g,g)) == (1,0,0,1)


def test_single_rational_2torsion_gives_group_order_two():
    # x(x^2+x+1)
    r=audit_weierstrass_2torsion({"a2":1,"a4":1,"a6":0})
    assert r["rational_2torsion_x"] == ["0"]
    assert r["generated_action_group_order"] == 2


def test_recover_action_from_exact_samples():
    samples=[{"x":"2","image":"-1/2"},{"x":"3","image":"-1/3"},{"x":"5","image":"-1/5"},{"x":"7","image":"-1/7"}]
    r=recover_pgl2_from_samples(samples)
    assert r["samples_verified"] == 4
    assert matrix_signature(r["pgl2_matrix"]) == matrix_signature([0,-1,1,0])


def test_chart_orbit_reducer_collapses_group_members():
    actions=audit_weierstrass_2torsion({"a2":0,"a4":-1,"a6":0})
    charts=[
        {"id":"I","matrix":[1,0,0,1]},
        {"id":"g0","matrix":[0,-1,1,0]},
        {"id":"g1","matrix":[1,1,1,-1]},
        {"id":"g2","matrix":[-1,1,1,1]},
    ]
    r=chart_audit_from_payload({"charts":charts},actions,coordinate_label="weierstrass x")
    assert r["input_charts"] == 4
    assert r["unique_chart_orbits"] == 1
    assert r["searches_saved_if_one_per_observed_orbit"] == 3
    assert r["savings_percent"] == 75.0


def test_unrelated_chart_forms_second_orbit():
    actions=audit_weierstrass_2torsion({"a2":0,"a4":-1,"a6":0})
    charts=[
        {"id":"I","matrix":[1,0,0,1]},
        {"id":"g0","matrix":[0,-1,1,0]},
        {"id":"other","matrix":[2,1,1,1]},
    ]
    r=chart_audit_from_payload({"charts":charts},actions)
    assert r["unique_chart_orbits"] == 2
    assert r["redundant_input_charts"] == 1


def test_float_rejected():
    import pytest
    from engine import q, SymmetryError
    with pytest.raises(SymmetryError): q(0.5)


def test_extension_backend_does_not_collide_with_generic_engine_module():
    """Regression: another extension may already own sys.modules['engine']."""
    import importlib.util
    import sys
    import types

    fake = types.ModuleType("engine")
    fake.marker = "wrong-extension-engine"
    previous = sys.modules.get("engine")
    sys.modules["engine"] = fake
    try:
        extension_path = HERE / "extension.py"
        name = "rank42_extension_torsion_symmetry_reducer_regression_test"
        spec = importlib.util.spec_from_file_location(name, extension_path)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.SymmetryError.__module__ == "rank42_extension_torsion_symmetry_reducer_engine"
        assert callable(mod.audit_weierstrass_2torsion)
    finally:
        if previous is None:
            sys.modules.pop("engine", None)
        else:
            sys.modules["engine"] = previous
