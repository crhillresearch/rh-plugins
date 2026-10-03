from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "extension.py").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))


def test_manifest_declares_workspace_extension():
    assert MANIFEST["plugin_type"] == "extension"
    assert MANIFEST["id"] == "fiber_atlas"
    assert MANIFEST["name"] == "Fiber Atlas"
    assert MANIFEST["version"] == "0.4.1"
    assert MANIFEST["menu"]["section"] == "Analysis"
    assert MANIFEST["icon"] == ":material/map:"
    assert MANIFEST["menu"]["icon"] == ":material/map:"


def test_workspace_uses_core_owned_page_header():
    assert 'st.title("Fiber Atlas")' not in SOURCE


def test_workspace_is_explicitly_read_only_and_proof_conservative():
    assert "Fiber Atlas is read-only" in SOURCE
    assert "research/scheduling " in SOURCE
    assert "signals, not proofs" in SOURCE
    assert "does not execute searches or modify rank evidence" in SOURCE
    forbidden = re.compile(r'context\.db\.execute\(\s*["\']\s*(INSERT|UPDATE|DELETE|REPLACE)', re.I)
    assert not forbidden.search(SOURCE)


def test_landscape_is_theme_aware_without_external_plotting_dependency():
    assert "fa-chart-shell" in SOURCE
    assert "var(--rh-card)" in SOURCE
    assert "var(--rh-border)" in SOURCE
    assert "var(--rh-primary)" in SOURCE
    assert "<title>{title}</title>" in SOURCE
    assert "plotly" not in SOURCE.lower()
    assert "seaborn" not in SOURCE.lower()


def test_workspace_exposes_family_axes_and_color_controls():
    assert 'st.selectbox(\n        "Family"' in SOURCE
    assert '"X axis"' in SOURCE
    assert '"Y axis"' in SOURCE
    assert '"Color"' in SOURCE
    assert "B.PLOT_METRICS" in SOURCE
    assert "B.COLOR_METRICS" in SOURCE


def test_curve_handoff_uses_the_existing_curves_route_contract():
    assert 'st.session_state["curves_selected_id"]' in SOURCE
    assert 'st.session_state["curves-filter"] = ""' in SOURCE
    assert 'st.session_state["curves-minrank"] = 0' in SOURCE
    assert 'st.session_state["curves-family"] = "All"' in SOURCE
    assert 'st.session_state["curves-evidence"] = "Any"' in SOURCE
    assert 'st.session_state["curves-status"] = "Any"' in SOURCE
    assert 'st.session_state["rh_page"] = "Curves"' in SOURCE
    assert "st.rerun()" in SOURCE


def test_workspace_does_not_become_a_search_engine():
    assert "Open selected curve" in SOURCE
    assert "Target Search" in SOURCE
    assert "route_curve_to_target" in SOURCE
    assert "route_selection_to_pipelines" in SOURCE
    assert "pipeline_runner" not in SOURCE
    assert "candidate_generate" not in SOURCE
    assert "launch_with_pipeline" not in SOURCE
    assert "create_pipeline_run" not in SOURCE


def test_workspace_exposes_research_modes():
    assert 'views = ["Landscape", "Farey / denominator", "Rank jumps", "Search yield"]' in SOURCE
    assert 'st.segmented_control(' in SOURCE
    assert 'if view == "Search yield":' in SOURCE
    assert '"Rational numerator/denominator geometry.' in SOURCE
    assert '"Yield measure"' in SOURCE


def test_workspace_exposes_read_only_filters():
    assert '"Root number"' in SOURCE
    assert '"Rank status"' in SOURCE
    assert '"Rigorous lower band"' in SOURCE
    assert '"log rational height band"' in SOURCE
    assert '"log denominator band"' in SOURCE
    assert "B.filter_records(" in SOURCE


def test_workspace_exposes_durable_search_yield_and_bad_prime_views():
    assert '"Exact discoveries"' in SOURCE
    assert '"Quartic hits"' in SOURCE
    assert '"Covering mapped"' in SOURCE
    assert '"Rigorous point witnesses"' in SOURCE
    assert '"Bad-prime fingerprint"' in SOURCE
    assert "B.bad_prime_fingerprint(enriched)" in SOURCE
    assert "descriptive only" in SOURCE


def test_workspace_bounds_large_svg_payload():
    assert "B.bound_plotted(raw_plotted, max_points=800)" in SOURCE
    assert "bounded display preserves high-signal fibers" in SOURCE


def test_workspace_uses_core_owned_research_handoff_contract():
    assert "from rank42.ui_handoffs import (" in SOURCE
    assert "normalize_research_handoff" in SOURCE
    assert "route_curve_to_target" in SOURCE
    assert "route_selection_to_pipelines" in SOURCE
    assert 'st.session_state["byo-target-mode"]' not in SOURCE
    assert 'st.session_state["byo-curve"]' not in SOURCE


def test_selection_panel_is_explicit_bounded_and_inspectable():
    assert 'MAX_HANDOFF_FIBERS = 250' in SOURCE
    assert '"Current filtered region"' in SOURCE
    assert '"Chosen fibers"' in SOURCE
    assert '"Primary fiber"' in SOURCE
    assert '"Target Search"' in SOURCE
    assert '"Pipelines"' in SOURCE
    assert '"Inspect handoff"' in SOURCE
    assert 'st.json(normalized)' in SOURCE
    assert "selection_hash" in SOURCE
    assert "Repeating the same selection produces the same hash." in SOURCE


def test_pipeline_handoff_is_context_only_not_execution():
    assert "Carries the explicit region into Pipelines as context." in SOURCE
    assert "It does not change Builder modules or candidate sources." in SOURCE
    assert "pipeline_runner" not in SOURCE
    assert "candidate_generate" not in SOURCE


def test_bad_prime_section_has_spacing_below_chart():
    assert ".fa-post-chart-gap{height:1rem}" in SOURCE
    gap = "<div class='fa-post-chart-gap' aria-hidden='true'></div>"
    call = """    _prime_fingerprint(
        filtered,
        db=context.db,
        family=family,
    )"""
    assert gap in SOURCE
    assert call in SOURCE
    assert SOURCE.index(gap) < SOURCE.index(call)


def test_old_core_handoff_compatibility_is_packaged():
    compat = ROOT / "handoff_compat.py"
    assert compat.is_file()
    text = compat.read_text(encoding="utf-8")
    assert 'state["analysis_active_curve_id"] = curve_id' in text
    assert 'state["target_curve_id"] = curve_id' in text
    assert 'state["rh_page"] = "Target"' in text
    assert 'state["rh_page"] = "Pipelines"' in text
    assert "create_pipeline_run" not in text
    assert "pipeline_runner" not in text


def test_extension_prefers_core_handoffs_but_has_old_core_fallback():
    assert "try:" in SOURCE
    assert "from rank42.ui_handoffs import (" in SOURCE
    assert 'except ModuleNotFoundError as exc:' in SOURCE
    assert 'if exc.name != "rank42.ui_handoffs":' in SOURCE
    assert '"handoff_compat.py"' in SOURCE
    assert 'HANDOFF_OWNER = "core"' in SOURCE
    assert 'HANDOFF_OWNER = "compat"' in SOURCE


def test_large_family_switch_keeps_search_yield_lazy():
    assert 'project_root=getattr(context, "project_root", Path.cwd())' in SOURCE
    assert "include_signals=True" not in SOURCE
    assert "Search-yield history is intentionally lazy on large databases." in SOURCE
    assert '"Load search-yield history"' in SOURCE
    assert "B.load_search_yield_signals(context.db, family)" in SOURCE
    assert "B.apply_search_yield_signals(filtered, signal_cache)" in SOURCE


def test_large_family_rendering_is_bounded():
    assert "B.bound_plotted(raw_plotted, max_points=800)" in SOURCE
    assert "table_rows = ordered[:1000]" in SOURCE
    assert "Showing the first" in SOURCE


def test_bad_prime_fingerprint_is_lazy_on_large_databases():
    assert "Bad-prime metadata is intentionally lazy on large databases." in SOURCE
    assert '"Load bad-prime fingerprint"' in SOURCE
    assert "B.load_bad_prime_signals(db, family)" in SOURCE
    assert "B.apply_bad_prime_signals(records, prime_cache)" in SOURCE
    assert "st.rerun()" in SOURCE



def test_workspace_displays_authoritative_family_baseline_semantics():
    assert '"Family baseline"' in SOURCE
    assert '"Baseline-excess fibers"' in SOURCE
    assert '"Max baseline excess"' in SOURCE
    assert '"Rank-jump fibers"' in SOURCE
    assert '"Max rank jump"' in SOURCE
    assert "baseline_kind == \"exact_generic_rank\"" in SOURCE
    assert "family baseline source:" in SOURCE


def test_lower_bound_baseline_is_not_mislabeled_as_exact_rank_jump():
    assert "Recorded generic baseline is a rigorous lower bound" in SOURCE
    assert "not by themselves proof of the jump above the unknown exact generic rank" in SOURCE
    assert "Baseline-excess axis = specialization rigorous lower" in SOURCE
    assert "proof-conservative excess, not an exact generic-rank jump" in SOURCE


def test_exact_generic_baseline_can_be_labeled_rank_jump():
    assert "Generic rank is exact at" in SOURCE
    assert "genuine rigorous rank jumps" in SOURCE
    assert "Rank-jump axis = specialization rigorous lower" in SOURCE


def test_family_load_receives_project_root_for_manifest_baseline_resolution():
    assert "records = B.load_family(" in SOURCE
    assert "context.db," in SOURCE
    assert "family," in SOURCE
    assert 'project_root=getattr(context, "project_root", Path.cwd())' in SOURCE



def test_old_core_compat_preserves_baseline_provenance_fields():
    text = (ROOT / "handoff_compat.py").read_text(encoding="utf-8")
    assert '"family_baseline"' in text
    assert '"family_baseline_kind"' in text
    assert '"baseline_excess"' in text



def test_inspect_labels_respect_exact_vs_lower_bound_baseline_semantics():
    assert "f\"{'jump' if record.baseline_is_exact else 'excess'} \"" in SOURCE
    assert 'f"jump {record.rank_jump' not in SOURCE
