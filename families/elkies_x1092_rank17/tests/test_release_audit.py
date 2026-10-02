from __future__ import annotations

import json
from pathlib import Path

import rank42.family_loader as family_loader
from rank42.plugins import get_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_is_mw17_only_and_current_core():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "elkies_x1092_rank17"
    assert manifest["name"] == "Elkies X1092 · Published MW17"
    assert manifest["version"] == "1.2.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 17
    assert manifest["historical_generic_rank_lower"] == 17
    assert manifest["verified_generic_rank_lower"] == 17
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert manifest["capabilities"] == ["candidate_generation", "free_search"]

    provenance = manifest["provenance"]
    assert provenance["arxiv"] == "2608.25406v1"
    assert provenance["date"] == "2026-08-26"
    assert provenance["doi"] == "10.48550/arXiv.2608.25406"
    assert provenance["theorem_reference"] == "Theorem 4 and §2.2"
    assert provenance["published_height_gram_determinant"] == 948
    assert "MW17 only" in provenance["release_scope"]


def test_release_package_excludes_quadratic_rank_jump_tooling():
    removed = [
        "base_change_common.py",
        "family_qbc1.py",
        "family_qbc2.py",
        "half_lattice.py",
        "identify_qbc_trace.py",
        "qbc_section_sampler.py",
        "qbc_trace_quartic_search.py",
        "reconstruct_qbc_section.py",
        "search_adapter.py",
        "solve_qbc11_section.py",
        "tests/test_rank_jump_base_changes.py",
    ]
    assert all(not (ROOT / rel).exists() for rel in removed)


def test_current_core_validates_published_mw17_package(tmp_path, monkeypatch):
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    (plugins_root / "elkies_x1092_rank17").symlink_to(
        ROOT,
        target_is_directory=True,
    )

    monkeypatch.setattr(
        family_loader,
        "_project_root",
        lambda project_root=None: tmp_path,
    )

    plugin = get_plugin(tmp_path, "elkies_x1092_rank17")
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "1.2.0"
    assert result["family_name"] == "Elkies X1092 published rank-17 fibration"
    assert result["family_generic_rank"] == 17
    assert result["validation_discriminant_nonzero"] is True

    certificate = result["variants"][0]["generic_rank_certificate"]
    assert certificate["verified"] is True
    assert certificate["lower_bound"] == 17
    assert certificate["details"]["height_gram_matches_published"] is True
    assert certificate["details"]["height_gram_determinant"] == "948"
