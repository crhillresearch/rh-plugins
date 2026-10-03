from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "extension.py").read_text(encoding="utf-8")


def test_extension_uses_core_owned_page_header():
    assert 'st.title("Curve Explorer")' not in SOURCE


def test_extension_uses_current_streamlit_iframe_api():
    assert "streamlit.components.v1" not in SOURCE
    assert "st.iframe(" in SOURCE


def test_extension_declares_supported_navigation_icon():
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["icon"] == ":material/insights:"
    assert manifest["menu"]["icon"] == ":material/insights:"


def test_extension_iframe_uses_rank_hunter_theme_tokens():
    assert 'st.session_state.get("_rh_theme_palette")' in SOURCE
    assert 'st.session_state.get("_rh_appearance")' in SOURCE
    assert '"ui_appearance"' in SOURCE
    assert '"rh-card"' in SOURCE
    assert '"rh-text"' in SOURCE
    assert '"rh-primary"' in SOURCE
    assert '"rh-success"' in SOURCE
    assert '"rh-warning"' in SOURCE
    assert '"rh-danger"' in SOURCE
    assert "--paper:var(--rh-card)" in SOURCE
    assert "--curve:var(--rh-primary)" in SOURCE
    assert "--stored:var(--rh-success)" in SOURCE
    assert "__THEME_CSS__" in SOURCE
    html = SOURCE[SOURCE.index("HTML_TEMPLATE") :]
    assert "background:#0f151f" not in html


def test_curve_explorer_manifest_keeps_theme_aware_description():
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "theme-aware plotting" in manifest["description"]


def test_point_clicks_assign_p_and_q_across_full_marker_hit_area():
    assert "'pointer-events':'all'" in SOURCE
    assert "for(const target of [halo,dot])" in SOURCE
    assert "target.addEventListener('click',click)" in SOURCE
    assert "selectPoint(String(p.id))" in SOURCE
    assert "if(p.interactive===false){showPoint" not in SOURCE
    assert "exact playback computed on selection" in SOURCE
    assert "outside the precomputed cache, so exact playback was computed on selection" in SOURCE


def test_curve_explorer_manifest_keeps_reliable_point_selection_description():
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert "reliable P/Q selection" in manifest["description"]


def test_uncached_selected_pairs_get_exact_client_side_playback():
    assert "function exactConstruction(P,Q)" in SOURCE
    assert "DATA.ainv_exact.map(qparse)" in SOURCE
    assert "function qparse(value)" in SOURCE
    assert "BigInt(parts[0])" in SOURCE
    assert "function currentPair()" in SOURCE
    assert "dynamicPairCache[key]=exactConstruction(P,Q)" in SOURCE
    assert "playBtn.disabled=!(P&&Q&&currentPair())" in SOURCE
    assert "precomputed exact cache" in SOURCE
    assert "uncached pairs computed exactly on selection" in SOURCE


def test_curve_explorer_manifest_bumps_for_graph_and_3d_views():
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.5.0"
    assert "complex affine 3D projection" in manifest["description"]
    assert "exact cached or on-selection" in manifest["description"]


def test_curve_explorer_has_lazy_graph_and_3d_page_views():
    assert 'options = ["Graph", "3D"]' in SOURCE
    assert 'variant="page"' in SOURCE
    assert 'if view == "3D":' in SOURCE
    assert "_render_3d_view(context, model, points)" in SOURCE
    assert "_render_graph_view(context, row, model, points)" in SOURCE
    assert "st.tabs(" not in SOURCE


def test_complex_3d_view_is_interactive_and_theme_aware():
    assert "HTML_3D_TEMPLATE" in SOURCE
    assert "Complex affine curve · R³ projection" in SOURCE
    assert "(Re x, Im x, Re y)" in SOURCE
    assert "(Re x, Im x, Im y)" in SOURCE
    assert 'data-proj="re"' in SOURCE
    assert 'data-proj="im"' in SOURCE
    assert "Auto rotate" in SOURCE
    assert "Reset view" in SOURCE
    assert "canvas.addEventListener('pointermove'" in SOURCE
    assert "canvas.addEventListener('wheel'" in SOURCE
    assert "--surface-a:var(--rh-primary)" in SOURCE
    assert "--real:var(--rh-danger)" in SOURCE
    assert "--stored:var(--rh-success)" in SOURCE


def test_3d_view_states_visualization_boundary():
    assert "Complex affine visualization only — not rank evidence." in SOURCE
    assert "point at infinity is omitted" in SOURCE
    assert "projection artifacts" in SOURCE


def test_graph_legend_is_outside_plotting_surface():
    legend = '<div class="graph-legend">'
    canvas = '<div class="canvas-wrap">'
    svg = '<svg id="plot"'
    assert legend in SOURCE
    assert SOURCE.index(legend) < SOURCE.index(canvas) < SOURCE.index(svg)
    assert ".graph-legend{display:flex" in SOURCE
    assert ".graph-legend{position:absolute" not in SOURCE
