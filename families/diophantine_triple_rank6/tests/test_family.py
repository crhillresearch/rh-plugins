import sys
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
from sage.all import QQ
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import family

def test_control_has_c2xc2_and_six_sections():
    c=family.construction_check(5)
    assert c["sections"]==6
    assert c["distinct_nonzero"]==6
    assert c["torsion_invariants"]==[2,2]

def test_original_paper_positive_x6_sign():
    v=QQ(5)
    E=family.curve(v)
    xplus=QQ(family._x_sections(v)[5])
    rhs=xplus**3+family.a_coeff(v)*xplus**2+family.b_coeff(v)*xplus
    assert family._sqrt_qq(rhs)**2==rhs
    xminus=-xplus
    rhsminus=xminus**3+family.a_coeff(v)*xminus**2+family.b_coeff(v)*xminus
    with pytest.raises(ArithmeticError):
        family._sqrt_qq(rhsminus)

def test_exact_generic_lower_six():
    c=family.validate_generic_rank_claim()
    assert c["verified"] is True
    assert c["lower_bound"]>=6
    assert c["details"]["control_parameter"]=="5"
    assert c["details"]["section_count"]==6

def test_finite_field_model():
    assert any(family.curve_mod_p(r,101) is not None for r in range(1,20))
