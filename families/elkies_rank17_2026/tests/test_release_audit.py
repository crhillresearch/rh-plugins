from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from rank42.plugins import get_plugin, validate_plugin
import rank42.family_loader as family_loader


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_matches_paper_and_current_core_line():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "elkies_rank17_2026"
    assert manifest["name"] == "Elkies Rank-17 K3"
    assert manifest["version"] == "1.3.1"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 17

    provenance = manifest["provenance"]
    assert provenance["author"] == "Noam D. Elkies"
    assert provenance["arxiv"] == "2608.25406v1"
    assert provenance["date"] == "2026-08-26"
    assert provenance["doi"] == "10.48550/arXiv.2608.25406"
    assert provenance["theorem_reference"] == "Theorem 4 and §2.2"
    assert "determinant 948" in provenance["claim"]
    assert provenance["release_audit_baseline"] == (
        "36d37730ded550a04ceb383434c466afd81e54c9"
    )

    assert manifest["known_controls"] == [
        {"t": "-2/377", "rank_lower": 25},
        {"t": "-308/251", "rank_lower": 26},
        {"t": "2456/135", "rank_lower": 27},
        {"t": "-9529/5471", "rank_lower": 28},
    ]


def test_release_package_keeps_rank18_family_separate():
    assert not (ROOT / "data" / "rank18_first_cover.json").exists()
    assert not (ROOT / "verify_rank18_first_cover.py").exists()
    assert not (ROOT / "SHA256SUMS.json").exists()


def test_current_core_validates_rank17_package(tmp_path, monkeypatch):
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    (plugins_root / "elkies_rank17_2026").symlink_to(
        ROOT,
        target_is_directory=True,
    )

    monkeypatch.setattr(
        family_loader,
        "_project_root",
        lambda project_root=None: tmp_path,
    )

    plugin = get_plugin(tmp_path, "elkies_rank17_2026")
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "1.3.1"
    assert result["family_name"] == "Elkies 2026 rank-17 K3"
    assert result["family_generic_rank"] == 17
    assert result["validation_parameter"] == "0"
    assert result["validation_discriminant_nonzero"] is True
    assert result["adapter_contract"]["api_version"] == 1
    assert result["symbolic_validation"]["sections_verified_on_curve"] == 17


def test_exact_height_gram_self_check_matches_paper():
    env = os.environ.copy()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "verify_family.py")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "sections_verified_on_curve" in proc.stdout
    assert "published height Gram: MATCH" in proc.stdout
    assert "determinant: 948" in proc.stdout
    assert "sections: 17" in proc.stdout
