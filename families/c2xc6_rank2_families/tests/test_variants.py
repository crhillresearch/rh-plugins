import importlib.util
from pathlib import Path
import pytest
pytest.importorskip("sage.all")

ROOT=Path(__file__).resolve().parents[1]
CASES={"dp1":"15","dp2":"17","dp3":"22","hadano":"19","new1":"20"}

def test_all_variant_sources_compile_before_math():
    for name in CASES:
        path=ROOT/"variants"/f"{name}.py"
        compile(path.read_text(encoding="utf-8"),str(path),"exec")

def _load(name):
    p=ROOT/"variants"/f"{name}.py"
    s=importlib.util.spec_from_file_location(f"c2xc6_test_{name}",p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

@pytest.mark.parametrize("variant,control",CASES.items())
def test_paper_control_has_c2xc6_and_two_exact_sections(variant,control):
    c=_load(variant).construction_check(control)
    assert c["sections"]==2
    assert c["distinct_nonzero"]==2
    assert c["torsion_invariants"]==[2,6]

@pytest.mark.parametrize("variant,control",CASES.items())
def test_exact_generic_lower_bound_two(variant,control):
    c=_load(variant).validate_generic_rank_claim()
    assert c["verified"] is True
    assert c["lower_bound"]>=2
    assert c["details"]["control_parameter"]==control
    assert c["details"]["section_count"]==2

@pytest.mark.parametrize("variant",CASES)
def test_finite_field_candidate_model(variant):
    m=_load(variant)
    assert any(m.curve_mod_p(r,101) is not None for r in range(1,20))

def test_dp3_damaged_pdf_line_is_reconstructed_from_source_base_change():
    m=_load("dp3")
    for value in (1,2,7,22):
        assert m.source_reconstruction_check(value) is True
