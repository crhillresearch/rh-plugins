from pathlib import Path
import importlib.util

from sage.all import QQ

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dmt_triad_cef_certificate_test", ROOT / "cef_family.py"
)
CEF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CEF)


def test_rank10_certificate_points_are_available_on_both_canonical_aliases():
    for parameter in ("-327/136", "-463/191"):
        E = CEF.curve(parameter)
        points = CEF.certified_specialization_points(parameter)
        meta = CEF.certified_specialization_metadata(parameter)
        assert E is not None
        assert len(points) == 10
        assert len({(str(P[0]), str(P[1])) for P in points}) == 10
        assert all(P.curve() == E for P in points)
        assert meta["external_exact_rank_claim"] == 10
        assert meta["artifact_id"] == 10369247534


def test_rank10_certificate_is_not_exposed_on_unrelated_cef_parameter():
    assert CEF.certified_specialization_points(QQ("12/5")) == []
    assert CEF.certified_specialization_metadata(QQ("12/5")) == {}


def test_historical_rank9_and_rank8_bundles_match_exact_cef_models():
    historical = {
        "-61/16": 9,
        "-103/2": 8,
        "-327/13": 8,
        "-330/227": 8,
        "-76/27": 8,
        "-79/25": 8,
        "-90/89": 8,
        "-97/16": 8,
        "-97/58": 8,
    }
    for source_parameter, expected_rank in historical.items():
        source = QQ(source_parameter)
        alias = (source + 1) / (source - 1)
        source_E = CEF.curve(source)
        alias_E = CEF.curve(alias)
        assert source_E is not None and alias_E is not None
        assert list(source_E.a_invariants()) == list(alias_E.a_invariants())

        for parameter in (source, alias):
            E = CEF.curve(parameter)
            points = CEF.certified_specialization_points(parameter)
            meta = CEF.certified_specialization_metadata(parameter)
            assert len(points) == expected_rank
            assert len({(str(P[0]), str(P[1])) for P in points}) == expected_rank
            assert all(P.curve() == E for P in points)
            assert meta["external_exact_rank_claim"] == expected_rank
            assert meta["bundle_point_count"] == expected_rank
            assert meta["matched_by_exact_model"] is True


def test_historical_highrank_bundle_is_not_exposed_on_generic_control():
    assert CEF.certified_specialization_points(QQ("12/5")) == []
    assert CEF.certified_specialization_metadata(QQ("12/5")) == {}
