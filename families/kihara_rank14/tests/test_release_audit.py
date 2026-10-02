from __future__ import annotations

import json
from pathlib import Path

import rank42.family_loader as family_loader
from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_matches_kihara_rank14_theorem():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "kihara2001_rank14"
    assert manifest["name"] == "Kihara (2001)"
    assert manifest["version"] == "1.2.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"

    assert manifest["historical_generic_rank_lower"] == 14
    assert manifest["verified_generic_rank_lower"] == 14
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert "generic_rank" not in manifest

    provenance = manifest["provenance"]
    assert provenance["author"] == "Shoichi Kihara"
    assert provenance["doi"] == "10.3792/pjaa.77.50"
    assert "rank at least 14" in provenance["published_claim"]
    assert "t=2" in provenance["theorem_proof_control"]
    assert "221792776617402574.10" in provenance["published_height_determinant"]
    assert "not exact generic rank" in provenance["release_claim_boundary"]


def test_current_core_validates_exact_kihara_generic_lower_bound(tmp_path, monkeypatch):
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    (plugins_root / "kihara_rank14").symlink_to(ROOT, target_is_directory=True)

    monkeypatch.setattr(
        family_loader,
        "_project_root",
        lambda project_root=None: tmp_path,
    )

    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "1.2.0"
    assert result["default_variant"] == "default"
    assert result["validation_parameter"] == "1"
    assert result["validation_discriminant_nonzero"] is True

    certificate = result["variants"][0]["generic_rank_certificate"]
    assert certificate["verified"] is True
    assert certificate["lower_bound"] >= 14
    assert certificate["certificate_version"] == (
        "kihara2001-rank14-generic-lower-v1.2.0"
    )
    assert certificate["details"]["control_parameter"] == "2"
    assert certificate["details"]["section_count"] == 14

    assert result["adapter_contract"]["api_version"] == 1


def test_release_readme_is_portable_and_lower_bound_only():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Rank Hunter **0.9.2**" in readme
    assert "generic rank at least 14" in readme
    assert "Neither Kihara's paper nor this release" in readme
    assert "claims exact generic rank 14" in readme
    assert 'PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python' in readme

    assert "/home/" not in readme
    assert "/Users/" not in readme
    assert "miniforge3" not in readme
    assert "v0.8.7.1" not in readme


def test_stale_checksum_manifest_is_not_released():
    assert not (ROOT / "SHA256SUMS.txt").exists()
