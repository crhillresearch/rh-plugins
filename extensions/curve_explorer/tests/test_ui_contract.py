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


def test_curve_explorer_manifest_bumps_for_uncached_exact_playback():
    import json

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.4.8"
    assert "exact cached or on-selection" in manifest["description"]
