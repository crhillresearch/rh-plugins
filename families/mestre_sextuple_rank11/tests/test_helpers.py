from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("mestre_helpers_test", ROOT / "search_helpers.py")
h = module_from_spec(spec); spec.loader.exec_module(h)


def test_height_stage_parser():
    assert h.parse_height_stages("10000,1000,1000") == [1000, 10000]


def test_affine_key_identifies_sign_pair():
    assert h.canonical_affine_key("2/3", "-5/7") == h.canonical_affine_key("2/3", "5/7")


def test_projection_residual_screen():
    # basis [1,0], candidate [0,2] gives residual 4
    out = h.projection_residuals([[1.0, 0.0], [0.0, 4.0]], 1)
    assert len(out) == 1
    assert abs(out[0]["residual"] - 4.0) < 1e-12
