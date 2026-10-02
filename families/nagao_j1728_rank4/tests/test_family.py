import sys
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
from sage.all import QQ

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import family

def test_control_matches_nagao_source_exactly():
    c=family.construction_check(3)
    assert (c["a"],c["b"],c["c"],c["d"])==("133","-134","158","-59")
    assert c["k"]=="635318657"
    assert c["factorization_ok"] is True
    assert c["equal_biquadrates"] is True
    assert c["sections"]==4
    assert c["distinct_nonzero"]==4
    assert c["torsion_invariants"]==[2]
    assert c["j_invariant"]=="1728"

def test_factored_k_matches_source_construction():
    for t in (QQ(-7)/3,QQ(-1),QQ(0),QQ(1),QQ(3),QQ(11)/5):
        ident=family.source_identity_check(t)
        assert ident["equal_biquadrates"] is True
        assert ident["factorization"] is True

def test_exact_parameter_sign_symmetry():
    assert family.parameter_symmetry=="sign"
    for t in (QQ(1),QQ(3),QQ(7)/5):
        assert family.k_coeff(t)==family.k_coeff(-t)
        assert family.curve(t).a_invariants()==family.curve(-t).a_invariants()

def test_exact_generic_lower_four():
    c=family.validate_generic_rank_claim()
    assert c["verified"] is True
    assert c["lower_bound"]>=4
    assert c["details"]["control_parameter"]=="3"
    assert c["details"]["exact_generic_rank_claimed"] is False

def test_finite_field_model():
    assert any(family.curve_mod_p(r,101) is not None for r in range(1,20))
