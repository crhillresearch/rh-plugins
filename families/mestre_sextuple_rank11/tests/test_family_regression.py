import sys
from pathlib import Path
import pytest

pytest.importorskip("sage.all")
from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import family


def test_symbolic_square_completion_identity():
    result = family.validate_symbolically()
    assert result["identity_verified"] is True
    assert result["base_fibres_verified"] == 12
    assert result["sections_verified_on_curve"] == 11


def test_exact_specialization_and_sign_symmetry():
    result = family.construction_check(QQ(1))
    assert result["base_fibres"] == 12
    assert result["sections"] == 11
    assert result["distinct_nonzero"] == 11
    assert result["t_sign_quartic_symmetry"] is True
    assert family.parameter_orbit_key(QQ(-7)/QQ(3)) == "7/3"


def test_exact_generic_lower_bound_certificate():
    cert = family.validate_generic_rank_claim()
    assert cert["verified"] is True
    assert cert["lower_bound"] >= 11
    assert cert["certificate_version"] == "mestre-sextuple-rank11-generic-lower-v1.5.2"
    assert cert["details"]["control_parameter"] == "1"
    assert cert["details"]["section_count"] == 11
