from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from sage.all import QQ

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_manifest_matches_published_z2_rank9_family():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "elkies_klagsbrun_z2_rank9_2020"
    assert manifest["name"] == "Elkies-Klagsbrun Z/2 K3"
    assert manifest["version"] == "1.2.4"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 9
    assert manifest["historical_generic_rank_lower"] == 9
    assert manifest["generic_rank_claim_state"] == "sections_verified"
    assert "verified_generic_rank_lower" not in manifest

    provenance = manifest["provenance"]
    assert provenance["arxiv"] == "2003.00077"
    assert provenance["doi"] == "10.2140/obs.2020.4.233"
    assert provenance["arxiv_date"] == "2020-02-28"
    assert "Z/2Z × Z^9" in provenance["published_generic_group"]
    assert "-721141/2026305" in provenance["published_rank20_status"]
    assert "-68559/326291" in provenance["rank20_chart_note"]


def test_all_native_u_values_satisfy_published_admissibility_condition():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in manifest["variants"]}

    for variant_id in ("u11_5", "u2_5", "u2_13", "u22_13"):
        u = QQ(by_id[variant_id]["u"])
        value = QQ(5) - u * u
        assert u not in (QQ(1), QQ(-1), QQ(2), QQ(-2))
        assert value.is_square()


def test_current_core_validates_all_variants_charts_and_adapter():
    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "1.2.4"
    assert result["default_variant"] == "u11_5"
    assert [row["id"] for row in result["variants"]] == [
        "u11_5",
        "u2_5",
        "u2_13",
        "u22_13",
        "u11_5_published_chart_search",
    ]
    assert all(
        row["symbolic_validation"]["sections_verified_on_curve"] == 9
        for row in result["variants"]
    )
    assert all(row["validation_discriminant_nonzero"] for row in result["variants"])

    assert len(result["charts"]) == 1
    chart = result["charts"][0]
    assert chart["id"] == "published_u11_5"
    assert chart["variant_id"] == "u11_5_published_chart_search"
    assert chart["native_variant_id"] == "u11_5"
    assert chart["matrix"] == ["-1", "2", "1", "-6"]

    assert result["adapter_contract"]["api_version"] == 1


def test_release_self_check_replays_rank20_control():
    verifier = _load(
        "elkies_klagsbrun_release_verify",
        ROOT / "verify_family.py",
    )
    verifier.main()


def test_release_package_has_no_local_absolute_symlink_artifact():
    assert not (ROOT / "elkies_klagsbrun_z2_rank9_2020").exists()
