import sys
from pathlib import Path

import pytest

pytest.importorskip("sage.all")
from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import family


def test_published_model_control_r1():
    E = family.curve(QQ(1))
    assert E is not None
    assert E.a2() == QQ(144923576664714767187664476709689825)
    assert E.a4() == QQ(992142076008989538414086053669529971254077589006956592137177180160000)


def test_published_full_basis_and_order_four_torsion():
    check = family.construction_check(QQ(1))
    assert check["sections"] == 6
    assert check["distinct_nonzero"] == 6
    assert check["torsion_order"] == 4


def test_good_finite_field_screen():
    E = family.curve_mod_p(1, 101)
    assert E is not None
    assert E.discriminant() != 0


def test_exact_generic_lower_bound_certificate():
    cert = family.validate_generic_rank_claim()
    assert cert["verified"] is True
    assert cert["lower_bound"] >= 6
    assert cert["certificate_version"] == "dujella-peral-z4-rank6-generic-lower-v0.1.1"
    assert cert["details"]["control_parameter"] == "1"
    assert cert["details"]["section_count"] == 6
