import sys
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import family
def test_control_has_c2xc4_and_four_sections():
    c=family.construction_check(15); assert c["sections"]==4; assert c["distinct_nonzero"]==4; assert c["torsion_invariants"]==[2,4]
def test_independence_control_has_four_sections():
    c=family.construction_check(2); assert c["sections"]==4; assert c["distinct_nonzero"]==4
def test_exact_generic_lower_four():
    c=family.validate_generic_rank_claim(); assert c["verified"] is True; assert c["lower_bound"]>=4; assert c["details"]["control_parameter"]=="15"
def test_finite_field_model():
    assert any(family.curve_mod_p(r,101) is not None for r in range(1,20))
