import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fibonacci_triples_target_test", ROOT / "target_search.py")
target = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(target)


def test_candidate_record_preserves_exact_rational_parameter():
    rec = target.candidate_record("-85/38", 1.25)
    assert rec == {"a": -85, "b": 38, "score": 1.25}


def test_candidate_record_normalizes_integer_parameter():
    rec = target.candidate_record("3", None)
    assert rec == {"a": 3, "b": 1, "score": 0.0}


def test_target_parser_defaults_to_pari():
    args = target.parse_args(["--curve-id", "13", "--family", "fibonacci_triples_odd"])
    assert args.quick_strategy == "pari"
