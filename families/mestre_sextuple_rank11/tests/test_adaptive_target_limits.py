import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "mestre_search_adapter_test",
        ROOT / "search_adapter.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_record_hunt_uses_banded_promoted_laptop_safe_search():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    preset = next(rec for rec in manifest["search_presets"] if rec["id"] == "record_hunt")
    target = preset["target"]

    assert target["charts"] == 96
    assert target["timeout"] == 60
    assert target["nonintegral_timeout"] == 20
    assert target["nonintegral_timeout_limit"] == 3
    assert target["stages"] == "100000,1000000,10000000"
    assert target["banded_rational"] is True
    assert target["band_threshold"] == 10000000
    assert target["denominator_bands"] == "10000,100000,1000000,3000000,max"
    assert target["promotion_height"] == 10000000
    assert target["promotion_charts"] == 16


def test_deep_target_keeps_banding_ready_without_forcing_promotion():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    preset = next(rec for rec in manifest["search_presets"] if rec["id"] == "deep")
    target = preset["target"]

    assert target["nonintegral_timeout"] == 30
    assert target["nonintegral_timeout_limit"] == 3
    assert target["banded_rational"] is True
    assert target["band_threshold"] == 10000000
    assert target["promotion_height"] == 0
    assert target["promotion_charts"] == 0


def test_pgl2_adapter_forwards_banding_and_promotion_controls():
    adapter = _load_adapter()
    options = {
        "adapter": "pgl2",
        "limit": 1,
        "mode": "both",
        "charts": 96,
        "stages": "100000,1000000,10000000",
        "timeout": 60,
        "nonintegral_timeout": 20,
        "nonintegral_timeout_limit": 3,
        "banded_rational": True,
        "band_threshold": 10000000,
        "denominator_bands": "10000,100000,1000000,3000000,max",
        "promotion_height": 10000000,
        "promotion_charts": 16,
    }
    cmd = adapter.build_target_search_command(
        python="/science/python",
        db="/tmp/rank42.db",
        curve_id=3010,
        options=options,
    )

    assert "--nonintegral-timeout" in cmd
    assert cmd[cmd.index("--nonintegral-timeout") + 1] == "20"
    assert "--nonintegral-timeout-limit" in cmd
    assert cmd[cmd.index("--nonintegral-timeout-limit") + 1] == "3"
    assert "--banded-rational" in cmd
    assert cmd[cmd.index("--band-threshold") + 1] == "10000000"
    assert cmd[cmd.index("--denominator-bands") + 1] == "10000,100000,1000000,3000000,max"
    assert cmd[cmd.index("--promotion-height") + 1] == "10000000"
    assert cmd[cmd.index("--promotion-charts") + 1] == "16"


def test_chart_search_contains_persistent_bands_promotion_and_circuit_breaker():
    source = (ROOT / "chart_search.py").read_text(encoding="utf-8")

    assert "def _denominator_bands" in source
    assert '"denominator_band"' in source
    assert "chart_productivity" in source
    assert "[mestre promotion]" in source
    assert "[mestre bands]" in source
    assert "band_timeout_counts" in source
    assert "[mestre adaptive]" in source
    assert "continuing other bands/charts" in source



def test_fiber_expansion_preset_is_target_only_and_geometry_safe():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    preset = next(rec for rec in manifest["search_presets"] if rec["id"] == "fiber_expansion")
    target = preset["target"]

    assert "candidate" not in preset
    assert "family" not in preset
    assert target["chart_strategy"] == "fiber_expansion"
    assert target["exploratory_anchor_pool"] == 48
    assert target["exploratory_order"] == "newest_high_denominator"
    assert target["exploratory_mix"] == "balanced"
    assert target["banded_rational"] is True
    assert target["promotion_height"] == 10000000
    assert target["promotion_charts"] == 16


def test_pgl2_adapter_forwards_exploratory_geometry_controls():
    adapter = _load_adapter()
    options = {
        "adapter": "pgl2",
        "limit": 1,
        "mode": "both",
        "charts": 96,
        "chart_strategy": "fiber_expansion",
        "exploratory_anchor_pool": 48,
        "exploratory_order": "newest_high_denominator",
        "exploratory_mix": "balanced",
    }
    cmd = adapter.build_target_search_command(
        python="/science/python",
        db="/tmp/rank42.db",
        curve_id=3010,
        options=options,
    )

    assert cmd[cmd.index("--chart-strategy") + 1] == "fiber_expansion"
    assert cmd[cmd.index("--exploratory-anchor-pool") + 1] == "48"
    assert cmd[cmd.index("--exploratory-order") + 1] == "newest_high_denominator"
    assert cmd[cmd.index("--exploratory-mix") + 1] == "balanced"


def test_chart_search_keeps_exploratory_fibres_out_of_rank_evidence():
    source = (ROOT / "chart_search.py").read_text(encoding="utf-8")

    assert "rank_exploratory_geometry_charts" in source
    assert "geometry only; never rank evidence" in source
    assert "new_fiber_owner" in source
    assert "new_fiber_band_counts" in source
    assert "x not in existing_native_before" in source



def test_mestre_search_options_define_global_groups_and_field_help():
    adapter = _load_adapter()
    defs = adapter.search_options(context="target")

    assert defs
    assert all(rec.get("group") for rec in defs)
    assert all(rec.get("help") for rec in defs)
    assert all("group_expanded" in rec for rec in defs)

    groups = {rec["group"] for rec in defs}
    assert {
        "Search geometry",
        "Anchor geometry",
        "Exploratory geometry",
        "Search depth",
        "Banded rational search",
        "Exact verification",
    } <= groups

    collapsed = {
        rec["group"]
        for rec in defs
        if rec.get("group_expanded") is False
    }
    assert {
        "Anchor geometry",
        "Exploratory geometry",
        "Banded rational search",
        "Exact verification",
    } <= collapsed
