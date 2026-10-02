from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import rank42.family_loader as family_loader
from rank42.plugins import get_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ROOT.parent
R17 = FAMILIES / "elkies_rank17_2026"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_manifest_tracks_published_cover_and_current_core():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "elkies_rank18_2026"
    assert manifest["name"] == "Elkies Rank-18 First Cover"
    assert manifest["version"] == "0.1.1"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 18
    assert manifest["verified_generic_rank_lower"] == 18
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"

    provenance = manifest["provenance"]
    assert provenance["arxiv"] == "2608.25406v1"
    assert provenance["date"] == "2026-08-26"
    assert provenance["published_cover"] == (
        "u^2=4225*t^2+38636*t+289444"
    )
    assert provenance["parameterization"] == (
        "t=(289444-r^2)/(130*r-38636), u=65*t+r"
    )
    assert provenance["doi"] == "10.48550/arXiv.2608.25406"
    assert "equation (11)" in provenance["theorem_reference"]
    assert "rank at least 18" in provenance["published_claim"]


def test_rank17_release_dependency_is_explicit_and_available():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    dependency = manifest["provenance"]["rank17_dependency"]

    assert "Elkies Rank-17 K3" in dependency
    assert (R17 / "family.json").is_file()


def test_recovered_p18_is_exactly_verified_on_quadratic_cover():
    family = _load("elkies_rank18_release_family", ROOT / "rank18_family.py")

    symbolic = family.validate_symbolically()
    certificate = family.validate_generic_rank_claim()

    assert symbolic["parameterization_verified"] is True
    assert symbolic["sections_verified_on_curve"] == 18
    assert symbolic["recovered_p18_verified"] is True

    assert certificate["verified"] is True
    assert certificate["lower_bound"] == 18
    details = certificate["details"]
    assert details["quadratic_cover_field"] == "Q(t,u)"
    assert details["p18_exact_on_cover"] is True
    assert details["galois_anti_invariant_nonzero"] is True
    assert details["trace_identity_verified"] is True
    assert len(details["trace_basis_vector"]) == 17


def test_current_core_validates_rank18_package(tmp_path, monkeypatch):
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    (plugins_root / "elkies_rank17_2026").symlink_to(
        R17,
        target_is_directory=True,
    )
    (plugins_root / "elkies_rank18_2026").symlink_to(
        ROOT,
        target_is_directory=True,
    )

    monkeypatch.setattr(
        family_loader,
        "_project_root",
        lambda project_root=None: tmp_path,
    )

    plugin = get_plugin(tmp_path, "elkies_rank18_2026")
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "0.1.1"
    assert result["family_name"] == "Elkies 2026 rank-18 first quadratic cover"
    assert result["family_generic_rank"] == 18
    assert result["validation_parameter"] == "0"
    assert result["validation_discriminant_nonzero"] is True
    certificate = result["variants"][0]["generic_rank_certificate"]
    assert certificate["verified"] is True
    assert certificate["lower_bound"] == 18
    assert result["adapter_contract"]["api_version"] == 1


def test_adapter_keeps_family_and_target_search_package_local():
    adapter = _load("elkies_rank18_release_adapter", ROOT / "search_adapter.py")

    family_cmd = adapter.build_family_search_command(
        python="python",
        db="rank42.db",
        candidate_file="candidates.jsonl",
        options={"baseline_certificate": True, "limit": 2},
    )
    target_cmd = adapter.build_target_search_command(
        python="python",
        db="rank42.db",
        curve_id=123,
        options={"baseline_certificate": True},
    )

    assert str(ROOT / "family_search.py") in family_cmd
    assert "--baseline-certificate" in family_cmd
    assert family_cmd[-4:] == ["--input", "candidates.jsonl", "--limit", "2"]
    assert target_cmd[-2:] == ["--curve-id", "123"]
