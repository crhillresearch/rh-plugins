from fractions import Fraction
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_helpers():
    spec = importlib.util.spec_from_file_location("fermigier_subgroup_focus_test", ROOT / "subgroup_focus.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projection_residuals_distinguish_span_from_orthogonal_direction():
    helpers = _load_helpers()
    # basis height 4; first candidate is exactly half the basis vector;
    # second candidate is orthogonal with height 9.
    gram = [
        [4, 2, 0],
        [2, 1, 0],
        [0, 0, 9],
    ]
    rows = helpers.projection_residuals(gram, 1)
    assert rows[0]["residual"] == 0.0
    assert rows[0]["relative_residual"] == 0.0
    assert rows[1]["residual"] == 9.0
    assert rows[1]["relative_residual"] == 1.0


def test_projection_residuals_reject_singular_basis_instead_of_claiming_novelty():
    helpers = _load_helpers()
    gram = [
        [1, 1, 0],
        [1, 1, 0],
        [0, 0, 2],
    ]
    try:
        helpers.projection_residuals(gram, 2)
    except ValueError as exc:
        assert "positive definite" in str(exc)
    else:
        raise AssertionError("singular numerical basis should disable the novelty screen")


def test_spread_points_deduplicates_sign_and_spans_height_range():
    helpers = _load_helpers()
    points = [
        (Fraction(1, 2), Fraction(3, 2)),
        (Fraction(1, 2), Fraction(-3, 2)),
        (Fraction(2), Fraction(1)),
        (Fraction(10), Fraction(1)),
        (Fraction(100), Fraction(1)),
    ]
    deduped = helpers.spread_points(points, 10)
    assert len(deduped) == 4
    assert sum(1 for point in deduped if point[0] == Fraction(1, 2)) == 1

    selected = helpers.spread_points(points, 2)
    assert len(selected) == 2
    assert selected[-1][0] == Fraction(100)


def test_rank_novelty_puts_largest_relative_residual_first():
    helpers = _load_helpers()
    rows = [
        {"id": "a", "residual": 100.0, "relative_residual": 0.1},
        {"id": "b", "residual": 2.0, "relative_residual": 0.8},
        {"id": "c", "residual": 4.0, "relative_residual": 0.4},
    ]
    assert [row["id"] for row in helpers.rank_novelty(rows)] == ["b", "c", "a"]
