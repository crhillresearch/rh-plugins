import importlib.util
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
ROOT=Path(__file__).resolve().parents[1]
CASES={"dp1":"22","dp2":"19","new1":"11","macleod1":"17","macleod2":"3","new2":"-48","new3":"10"}
def _load(n):
    p=ROOT/"variants"/f"{n}.py"; s=importlib.util.spec_from_file_location(f"z8_test_{n}",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
@pytest.mark.parametrize("variant,control",CASES.items())
def test_control_has_c8_and_two_sections(variant,control):
    c=_load(variant).construction_check(control); assert c["sections"]==2 and c["distinct_nonzero"]==2 and c["torsion_invariants"]==[8]
@pytest.mark.parametrize("variant,control",CASES.items())
def test_exact_generic_lower_two(variant,control):
    c=_load(variant).validate_generic_rank_claim(); assert c["verified"] is True and c["lower_bound"]>=2 and c["details"]["control_parameter"]==control
@pytest.mark.parametrize("variant",CASES)
def test_finite_field_candidate_model(variant):
    m=_load(variant); assert any(m.curve_mod_p(r,101) is not None for r in range(1,20))
