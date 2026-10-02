from __future__ import annotations

from pathlib import Path
import json

from rank42.plugins import get_plugin, validate_plugin
import rank42.family_loader as family_loader


ROOT = Path(__file__).resolve().parents[1]


def test_release_docs_and_manifest_target_current_core():
    manifest = (ROOT / "plugin.json").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert '"version": "0.1.3"' in manifest
    assert '"minimum_rank_hunter_version": "0.9.2"' in manifest
    assert '"source_commit": "3f53baaedcbdb852e2e999578bf0f75850ad3e5f"' in manifest
    assert '"plugin_release_baseline_commit": "36d37730ded550a04ceb383434c466afd81e54c9"' in manifest
    assert "Rank Hunter **0.9.2**" in readme
    assert "optional" in readme.lower()
    assert "private" in readme.lower()
    assert "0.8.7.1" not in manifest
    assert "0.8.7.1" not in readme


def test_optional_private_corpus_is_explicitly_access_restricted():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    builder = (ROOT / "build_curves2.py").read_text(encoding="utf-8")

    corpus = manifest["corpora"][0]
    assert corpus["id"] == "curves2"
    assert "optional" in corpus["name"].lower()
    assert "optional" in corpus["description"].lower()
    assert "private" in corpus["description"].lower()
    assert "authenticated access" in corpus["description"].lower()
    assert corpus["builder"] == "build_curves2.py"
    assert 'SOURCE_REPO = "crhillresearch/dmt-rank-jumps"' in builder


def test_current_core_validates_all_six_variants(tmp_path, monkeypatch):
    plugins_root = tmp_path / "plugins"
    plugins_root.mkdir()
    (plugins_root / "dmt_triad_rank4").symlink_to(ROOT, target_is_directory=True)

    monkeypatch.setattr(
        family_loader,
        "_project_root",
        lambda project_root=None: tmp_path,
    )

    plugin = get_plugin(tmp_path, "dmt_triad_rank4")
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "0.1.3"
    assert [row["id"] for row in result["variants"]] == [
        "ace",
        "acf",
        "bde",
        "bdf",
        "bef",
        "cef",
    ]
    for row in result["variants"]:
        assert row["validation_discriminant_nonzero"] is True
        certificate = row["generic_rank_certificate"]
        assert certificate["verified"] is True
        assert certificate["lower_bound"] >= 4

    assert result["adapter_contract"]["api_version"] == 1
