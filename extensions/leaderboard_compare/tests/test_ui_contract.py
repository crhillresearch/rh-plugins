from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "extension.py").read_text(encoding="utf-8")


def test_manifest_declares_leaderboard_compare_workspace():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "leaderboard_compare"
    assert manifest["name"] == "Leaderboard Compare"
    assert manifest["version"] == "0.2.1"
    assert manifest["plugin_type"] == "extension"
    assert manifest["entrypoint"] == "extension.py"
    assert manifest["menu"]["label"] == "Leaderboard Compare"
    assert manifest["menu"]["section"] == "Analysis"
    assert manifest["icon"] == manifest["menu"]["icon"] == ":material/monitoring:"


def test_runtime_identity_is_renamed_from_icarm_charts():
    assert "rank42_leaderboard_compare_backend" in SOURCE
    assert "icarm_charts_" not in SOURCE
    assert "leaderboard-compare-" in SOURCE


def test_chart_uses_semantic_theme_tokens_not_fixed_dark_palette():
    for token in (
        "--rh-card",
        "--rh-card-2",
        "--rh-border",
        "--rh-border-strong",
        "--rh-control-border",
        "--rh-text",
        "--rh-text-secondary",
        "--rh-muted",
        "--rh-muted-2",
        "--rh-primary",
        "--rh-surface-active",
    ):
        assert token in SOURCE

    for legacy_color in (
        "#0b0f16",
        "#273142",
        "#38d6c3",
        "#748092",
        "#243140",
        "#81909f",
        "#657585",
        "#a7b2bd",
    ):
        assert legacy_color not in SOURCE


def test_all_input_control_types_have_scoped_theme_contract():
    assert 'st-key-leaderboard-compare-' in SOURCE
    for testid in (
        "stRadio",
        "stSlider",
        "stSelectbox",
        "stMultiSelect",
        "stCheckbox",
    ):
        assert testid in SOURCE

    assert '[data-baseweb="select"] > div' in SOURCE
    assert '[data-baseweb="tag"]' in SOURCE
    assert '[role="slider"]' in SOURCE
    assert "accent-color:var(--rh-primary)" in SOURCE


def test_extension_preserves_leaderboard_modes_and_sources():
    assert "def render(context):" in SOURCE
    assert "Best per rank" in SOURCE
    assert "Record frontier" in SOURCE
    assert "Rank Hunter" in SOURCE
    assert "ICARM" in SOURCE


def test_torsion_filter_is_exposed_in_the_workspace():
    assert '"Torsion group"' in SOURCE
    assert 'key="leaderboard-compare-torsion"' in SOURCE
    assert "B.torsion_groups(points)" in SOURCE
    assert "B.filter_torsion(points, torsion_choice)" in SOURCE
    assert "torsion {p.torsion_label or 'unknown'}" in SOURCE
    assert "<th>torsion</th>" in SOURCE
