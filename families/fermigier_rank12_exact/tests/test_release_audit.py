from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from sage.all import QQ

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def _load_family():
    path = ROOT / "family.py"
    spec = importlib.util.spec_from_file_location(
        "fermigier_mestre_release_family",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_manifest_separates_lower_bound_from_exact_rank_provenance():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["plugin_type"] == "family"
    assert manifest["id"] == "fermigier_rank12_exact"
    assert manifest["name"] == "Fermigier–Mestre K3"
    assert manifest["version"] == "1.1.0"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"

    assert manifest["generic_rank"] == 12
    assert manifest["historical_generic_rank_lower"] == 12
    assert manifest["verified_generic_rank_lower"] == 12
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert "proves only the lower bound" not in manifest["generic_rank_status"]

    provenance = manifest["provenance"]
    assert provenance["fermigier_doi"] == "10.4064/aa-82-4-359-363"
    assert "19754/39" in provenance["published_specialization"]
    assert "39508/39" in provenance["published_specialization"]
    assert "exactly 12" in provenance["external_exact_rank12_provenance"]
    assert "external_exact_rank12_provenance" in provenance
    assert "verified_generic_rank_exact" not in manifest


def test_symbolic_reconstruction_and_published_control_bridge():
    family = _load_family()

    symbolic = family.validate_symbolically()
    assert symbolic["identity_verified"] is True
    assert symbolic["quartic_points_verified"] == 13
    assert symbolic["sections_after_origin"] == 12

    u = QQ(19754) / QQ(39)
    assert family._literal_shift(u) == QQ(39508) / QQ(39)
    assert family.ROOTS == (0, 55, 314, 378, 1007, 1036)
    control = family.construction_check(u)
    assert control["base_fibres"] == 13
    assert control["sections"] == 12


def test_current_core_validates_generic_lower_bound_and_adapter():
    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)

    assert result["status"] == "ready"
    assert result["plugin_version"] == "1.1.0"
    assert result["default_variant"] == "default"
    assert result["family_generic_rank"] == 12
    assert result["validation_parameter"] == "1"
    assert result["validation_discriminant_nonzero"] is True

    certificate = result["variants"][0]["generic_rank_certificate"]
    assert certificate["verified"] is True
    assert certificate["lower_bound"] >= 12
    assert certificate["details"]["control_parameter"] == "7/3"
    assert certificate["details"]["section_count"] == 12

    assert result["adapter_contract"]["api_version"] == 1


def test_release_text_has_no_stale_08_compatibility_claim():
    texts = [
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / "search_adapter.py").read_text(encoding="utf-8"),
        (ROOT / "subgroup_focus.py").read_text(encoding="utf-8"),
    ]
    assert all("v0.8.7.1" not in text for text in texts)
