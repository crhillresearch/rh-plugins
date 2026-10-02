import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCurve:
    def a_invariants(self):
        return [0, 1, 0, 2, 3]


def install_exact_lb(monkeypatch, lower_bound):
    rank42 = types.ModuleType("rank42")
    rank42.__path__ = []
    exact_lb = types.ModuleType("rank42.exact_lb")

    def run_exact_certificate(ainvs, points, *, timeout):
        assert list(ainvs) == [0, 1, 0, 2, 3]
        assert timeout == 120
        return {
            "status": "certified_independent",
            "independent": True,
            "rank_lower_bound": lower_bound,
            "point_count": len(points),
        }

    exact_lb.run_exact_certificate = run_exact_certificate
    monkeypatch.setitem(sys.modules, "rank42", rank42)
    monkeypatch.setitem(sys.modules, "rank42.exact_lb", exact_lb)


def test_odd_generic_lower_claim_uses_exact_two_section_certificate(monkeypatch):
    odd = load_module("odd_family.py", "fibonacci_triples_odd_claim_test")
    monkeypatch.setattr(odd, "curve", lambda t: FakeCurve())
    monkeypatch.setattr(odd, "generic_section_points", lambda t: [(10, 20), (30, 40)])
    install_exact_lb(monkeypatch, 2)

    cert = odd.validate_generic_rank_claim()
    assert cert["verified"] is True
    assert cert["lower_bound"] == 2
    assert cert["details"]["control_parameter"] == "3"
    assert cert["details"]["section_count"] == 2
    assert cert["certificate_version"] == "fibonacci-triples-v0.1.3"


def test_even_generic_lower_claim_uses_exact_non_torsion_certificate(monkeypatch):
    even = load_module("even_family.py", "fibonacci_triples_even_claim_test")
    monkeypatch.setattr(even, "curve", lambda t: FakeCurve())
    monkeypatch.setattr(even, "generic_section_points", lambda t: [(10, 20)])
    install_exact_lb(monkeypatch, 1)

    cert = even.validate_generic_rank_claim()
    assert cert["verified"] is True
    assert cert["lower_bound"] == 1
    assert cert["details"]["control_parameter"] == "20/9"
    assert cert["details"]["section_count"] == 1
    assert cert["certificate_version"] == "fibonacci-triples-v0.1.3"
