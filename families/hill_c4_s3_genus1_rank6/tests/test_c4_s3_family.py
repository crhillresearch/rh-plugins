"""Exercise the genus-one parameter map and the bundled proof replay."""
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_smooth_witness_and_rank_certificate():
    spec = importlib.util.spec_from_file_location("hill_c4_s3_family", ROOT / "family.py")
    family = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(family)

    E = family.curve(2)
    assert E is not None and E.discriminant() != 0
    assert len(family.generic_section_points(2)) == 8
    assert list(map(int, E.torsion_subgroup().invariants())) == [4]
    assert family.validate_generic_rank_claim()["lower_bound"] == 6
