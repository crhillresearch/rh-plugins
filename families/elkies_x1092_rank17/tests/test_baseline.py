from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from sage.all import QQ, ZZ, matrix

ROOT = Path(__file__).resolve().parents[1]


def load_family():
    path = ROOT / "family.py"
    spec = importlib.util.spec_from_file_location("elkies_x1092_rank17_test_family", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_published_mw17_symbolic_sections_and_gram():
    family = load_family()
    result = family.validate_symbolically()
    certificate = family.validate_generic_rank_claim()

    assert result["generic_rank_declared"] == 17
    assert result["sections_verified_on_curve"] == 17
    assert result["x_degrees"] == [4] * 17
    assert result["y_degrees"] == [6] * 17
    assert matrix(ZZ, family.PUBLISHED_GENERIC_GRAM).det() == 948

    assert certificate["verified"] is True
    assert certificate["lower_bound"] == 17
    assert certificate["details"]["height_gram_matches_published"] is True
    assert certificate["details"]["height_gram_determinant"] == "948"


def test_published_mw17_specialization_replays_all_labeled_sections():
    family = load_family()
    t = QQ(647) / 167
    E = family.curve(t)
    points = family.generic_section_points(t)
    metadata = family.generic_section_metadata(t)

    assert E is not None
    assert len(points) == 17
    assert len(metadata) == 17
    assert all(P in E for P in points)
    assert [rec["basis_label"] for rec in metadata] == [f"S{i}" for i in range(1, 18)]
    assert all(len(rec["coefficient_vector"]) == 17 for rec in metadata)
    assert all(sum(abs(v) for v in rec["coefficient_vector"]) == 1 for rec in metadata)
    assert [rec["leading_y_sign"] for rec in metadata] == list("-+-+++++-+-+++-++")
    assert all(len(rec["trace_coordinates"]) == 2 for rec in metadata)


def test_manifest_declares_verified_published_mw17_and_sampled_record_scan():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.3.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 17
    assert manifest["verified_generic_rank_lower"] == 17
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert manifest["family"]["kind"] == "module"
    assert manifest["provenance"]["published_height_gram_determinant"] == 948
    assert manifest["provenance"]["generic_basis_status"] == "published_exact_sections_bundled_and_height_gram_reverified"
    assert manifest["capabilities"] == [
        "candidate_generation",
        "family_search",
        "target_search",
        "known_subgroup",
        "free_search",
    ]
    assert manifest["search_adapter"] == "search_adapter.py"
    assert "variants" not in manifest
    defaults = manifest["candidate_defaults"]
    assert defaults["engine"] == "sampled"
    assert defaults["b_max"] == 1000000
    assert defaults["stage_bounds"] == "523,5000"
    assert defaults["stage_keeps"] == "50000,5000"


def test_fast_nagao_table_matches_exact_curve_counts():
    import math
    family = load_family()
    for p in (5, 7, 11, 13):
        table = family.nagao_score_table(p)
        assert len(table) == p
        for r in range(p):
            E = family.curve_mod_p(r, p)
            if E is None:
                assert table[r] is None
            else:
                assert table[r] is not None
                assert abs(table[r] - math.log(int(E.cardinality()) / p)) < 1e-12
