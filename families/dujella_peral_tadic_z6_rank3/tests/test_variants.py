import importlib.util
from pathlib import Path

import pytest
pytest.importorskip("sage.all")

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "lecacheux": "-7",
    "kihara": "15",
    "eroshkin_plus": "-11",
    "eroshkin_minus": "-15",
    "dujella_peral": "13",
    "macleod": "-30",
}


def _load(name):
    path = ROOT / "variants" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"dpt_test_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("variant,control", CASES.items())
def test_paper_control_has_c6_torsion_and_three_exact_sections(variant, control):
    mod = _load(variant)
    check = mod.construction_check(control)
    assert check["sections"] == 3
    assert check["distinct_nonzero"] == 3
    assert check["torsion_invariants"] == [6]


@pytest.mark.parametrize("variant,control", CASES.items())
def test_exact_generic_lower_bound_three(variant, control):
    mod = _load(variant)
    cert = mod.validate_generic_rank_claim()
    assert cert["verified"] is True
    assert cert["lower_bound"] >= 3
    assert cert["details"]["control_parameter"] == control
    assert cert["details"]["section_count"] == 3


@pytest.mark.parametrize("variant", CASES)
def test_finite_field_candidate_model(variant):
    mod = _load(variant)
    found = None
    for r in range(1, 20):
        E = mod.curve_mod_p(r, 101)
        if E is not None:
            found = E
            break
    assert found is not None
