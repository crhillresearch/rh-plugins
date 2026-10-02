import sys
from pathlib import Path
import pytest

pytest.importorskip("sage.all")
from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import family


def test_exact_section_and_quartic_interfaces():
    check = family.construction_check(QQ(2))
    assert check["sections"] == 14
    assert check["distinct_nonzero"] == 14
    assert len(family.native_quartic_known_points(QQ(2))) == 14
    assert len(family.quartic_search_coefficients(QQ(2))) == 5


def test_t_zero_is_excluded():
    with pytest.raises(ZeroDivisionError):
        family.quartic_search_coefficients(QQ(0))
