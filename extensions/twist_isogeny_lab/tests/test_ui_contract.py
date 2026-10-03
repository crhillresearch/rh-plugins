from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "extension.py").read_text(encoding="utf-8")
WORKER = (ROOT / "isogeny_worker.py").read_text(encoding="utf-8")
TWIST_WORKER = (ROOT / "twist_worker.py").read_text(encoding="utf-8")
PROBE_WORKER = (ROOT / "isogeny_probe_worker.py").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))


def test_manifest_declares_analysis_workspace():
    assert MANIFEST["plugin_type"] == "extension"
    assert MANIFEST["id"] == "twist_isogeny_lab"
    assert MANIFEST["version"] == "0.5.2"
    assert MANIFEST["menu"]["section"] == "Analysis"
    assert MANIFEST["icon"] == ":material/hub:"


def test_workspace_is_explicitly_on_demand_and_read_only():
    assert '"Compute full isogeny class"' in SOURCE
    assert "Runs only on request with a hard timeout." in SOURCE
    assert "does not create curves, run hunts, or promote rank claims" in SOURCE
    assert "does not insert it into the authoritative Rank Hunter database" in SOURCE


def test_workspace_uses_configured_scientific_python_worker():
    assert 'getattr(context, "science_python", "")' in SOURCE
    assert '"isogeny_worker.py"' in SOURCE
    assert "B.run_isogeny_worker(" in SOURCE
    assert '"Full-class timeout"' in SOURCE
    assert "[30, 90, 300, 900]" in SOURCE
    assert "timeout=full_timeout" in SOURCE


def test_worker_uses_exact_sage_isogeny_arithmetic():
    assert "from sage.all import EllipticCurve, QQ, ZZ" in WORKER
    assert "E = EllipticCurve([QQ(value) for value in raw])" in WORKER
    assert "iso = E.isogeny_class()" in WORKER
    assert "matrix = iso.matrix()" in WORKER
    assert "degree.is_prime()" in WORKER
    assert "curve.is_isomorphic(E)" in WORKER


def test_workspace_shows_graph_and_exact_arithmetic_metadata():
    assert "Rational isogeny graph" in SOURCE
    assert '"conductor"' in SOURCE
    assert '"discriminant"' in SOURCE
    assert '"j-invariant"' in SOURCE
    assert '"torsion invariants"' in SOURCE
    assert '"Direct prime-degree edges"' in SOURCE


def test_workspace_only_hands_off_retained_stored_matches():
    assert "stored_model_index" in SOURCE
    assert '"Open stored curve"' in SOURCE
    assert '"Target Search"' in SOURCE
    assert "route_curve_to_target" in SOURCE
    assert "No exact stored-model match for this node." in SOURCE


def test_workspace_does_not_launch_search_or_write_science():
    forbidden = (
        "pipeline_runner",
        "candidate_generate",
        "create_pipeline_run",
        "INSERT INTO",
        "UPDATE curves",
        "DELETE FROM",
    )
    for token in forbidden:
        assert token not in SOURCE



def test_workspace_projects_retained_source_and_exact_model_evidence():
    assert '"match type"' in SOURCE
    assert '"stored rigorous lower"' in SOURCE
    assert '"stored exact rank"' in SOURCE
    assert '"stored Nagao"' in SOURCE
    assert '"source Q-isomorphic"' in SOURCE
    assert '"exact model + source"' in SOURCE
    assert '"Retained curve match"' in SOURCE


def test_source_isomorphic_model_is_not_mislabeled_exact_model():
    assert "exactly Q-isomorphic to retained source" in SOURCE
    assert "rather than an exact-model match" in SOURCE



def test_workspace_exposes_bounded_quadratic_twist_view():
    assert '"Research view"' in SOURCE
    assert '"Quadratic twists"' in SOURCE
    assert '"Squarefree |d| bound"' in SOURCE
    assert '[25, 50, 100, 150, 250]' in SOURCE
    assert '"Compute quadratic twists"' in SOURCE
    assert "B.run_twist_worker(" in SOURCE
    assert '"twist_worker.py"' in SOURCE
    assert "timeout=120" in SOURCE


def test_twist_worker_uses_exact_squarefree_sage_twists():
    assert "ZZ(d).is_squarefree()" in TWIST_WORKER
    assert "E.quadratic_twist(ZZ(d))" in TWIST_WORKER
    assert "curve.global_minimal_model()" in TWIST_WORKER
    assert "minimal.root_number()" in TWIST_WORKER
    assert "minimal.conductor()" in TWIST_WORKER
    assert "conductor.prime_divisors()" in TWIST_WORKER


def test_twist_view_preserves_proof_boundary_and_retained_evidence_only():
    assert "Any visible association with stored rank or Nagao data is a research signal, not proof." in SOURCE
    assert '"stored rigorous lower"' in SOURCE
    assert '"stored exact rank"' in SOURCE
    assert '"stored Nagao"' in SOURCE
    assert "Viewing it does not insert" in SOURCE
    assert "a curve or rank evidence into Rank Hunter." in SOURCE



def test_large_curve_isogeny_timeout_is_inconclusive_with_exact_probe_fallback():
    assert '"Full-class timeout"' in SOURCE
    assert "[30, 90, 300, 900]" in SOURCE
    assert "except B.WorkerTimeout as exc:" in SOURCE
    assert "A timeout is inconclusive" in SOURCE
    assert "_render_isogeny_probe(" in SOURCE
    assert '"Run exact source probe"' in SOURCE
    assert '"timeout / unknown"' in SOURCE
    assert '"exact no hit"' in SOURCE


def test_probe_worker_checks_one_exact_prime_degree_at_a_time():
    assert "ALLOWED = {2, 3, 5, 7, 11, 13, 17, 19, 37, 43, 67, 163}" in PROBE_WORKER
    assert "sage_degree = ZZ(degree)" in PROBE_WORKER
    assert "E.isogenies_prime_degree(sage_degree)" in PROBE_WORKER
    assert "phi.codomain()" in PROBE_WORKER
    assert "codomain.global_minimal_model()" in PROBE_WORKER


def test_twist_table_compacts_large_arithmetic_but_detail_keeps_exact_values():
    assert '"N digits"' in SOURCE
    assert '"ω(N)"' in SOURCE
    assert '"support Δ"' in SOURCE
    assert "def _compact_integer(" in SOURCE
    assert "def _compact_primes(" in SOURCE
    assert '"Exact twist arithmetic"' in SOURCE
    assert '"conductor = "' in SOURCE
    assert '"discriminant = "' in SOURCE
    assert '"bad primes = ["' in SOURCE



def test_workspace_uses_core_owned_deterministic_research_handoffs():
    assert "normalize_research_handoff" in SOURCE
    assert "route_selection_to_pipelines" in SOURCE
    assert "set_research_handoff" in SOURCE
    assert 'f"hash: `{normalized[\'selection_hash\'][:16]}`"' in SOURCE
    assert '"Inspect normalized handoff"' in SOURCE
    assert '"Open in Pipelines"' in SOURCE


def test_twist_selection_handoff_preserves_exact_arithmetic_and_source_provenance():
    assert '"quadratic_twist_selection"' in SOURCE
    assert '"source_curve"' in SOURCE
    assert '"item_count"' in SOURCE
    assert '"minimal_a_invariants"' in SOURCE
    assert '"retained_curve_ids"' in SOURCE
    assert '"bound": int(bound)' in SOURCE
    assert '"root_filter": root_filter' in SOURCE
    assert '"retained_filter": stored_filter' in SOURCE


def test_isogeny_selection_handoff_preserves_class_and_probe_provenance():
    assert '"isogeny_class_selection"' in SOURCE
    assert '"class_complete": True' in SOURCE
    assert '"class_edges": list(payload.get("edges") or [])' in SOURCE
    assert '"isogeny_probe_selection"' in SOURCE
    assert '"class_complete": False' in SOURCE
    assert '"requested_degrees"' in SOURCE
    assert '"timed_out_degrees"' in SOURCE
    assert '"exact prime-degree source isogeny"' in SOURCE


def test_retained_target_and_curve_routes_receive_workspace_handoff():
    assert "_open_curve(target_record, handoff=current_handoff)" in SOURCE
    assert "handoff=current_handoff" in SOURCE
    assert "route_curve_to_target(" in SOURCE


def test_workspace_does_not_write_private_pipeline_builder_state():
    forbidden = (
        'st.session_state["byo-target-mode"]',
        'st.session_state["byo-curve"]',
        'st.session_state["byo_stages"]',
        "create_pipeline_run",
    )
    for token in forbidden:
        assert token not in SOURCE



def test_researcher_polish_puts_source_context_before_expensive_work():
    source_brief = '"Source arithmetic brief · "'
    assert source_brief in SOURCE
    assert '"a-invariants = ["' in SOURCE
    assert "Exact in this view:" in SOURCE
    assert SOURCE.index(source_brief) < SOURCE.index('"Compute full isogeny class"')
    assert SOURCE.index(source_brief) < SOURCE.index('"Compute quadratic twists"')


def test_researcher_polish_has_visibly_staged_workspace_hierarchy():
    assert "def _section_banner(" in SOURCE
    assert "til-stage-index" in SOURCE
    assert "til-boundary-grid" in SOURCE
    assert '"Source curve"' in SOURCE
    assert '"Research mode"' in SOURCE
    assert '"Selected twist"' in SOURCE
    assert '"Twist neighborhood"' in SOURCE
    assert '"Selected isogeny node"' in SOURCE
    assert '"Isogeny neighborhood"' in SOURCE
    assert "Session cache only" in SOURCE
    assert "Computed class data is session-cached only." in SOURCE


def test_research_mode_cards_and_timeout_control_keep_inline_spacing():
    assert "gap:.55rem;margin:.45rem 0 .65rem 0" in SOURCE
    assert 'format_func=lambda value: f"Timeout · {value}s"' in SOURCE
    assert 'label_visibility="collapsed"' in SOURCE


def test_selected_object_inspectors_precede_dense_result_views():
    twist_inspector = 'st.markdown("**Inspect one computed twist**")'
    twist_neighborhood = 'st.markdown("**Computed twist neighborhood**")'
    assert twist_inspector in SOURCE
    assert twist_neighborhood in SOURCE
    assert SOURCE.index(twist_inspector) < SOURCE.index(twist_neighborhood)

    isogeny_inspector = 'st.markdown("**Inspect one isogeny-class node**")'
    isogeny_graph = 'st.markdown("**Rational isogeny graph**")'
    assert isogeny_inspector in SOURCE
    assert isogeny_graph in SOURCE
    assert SOURCE.index(isogeny_inspector) < SOURCE.index(isogeny_graph)


def test_exact_detail_is_progressively_disclosed_but_preserved():
    assert 'with st.expander("Exact twist arithmetic", expanded=False):' in SOURCE
    assert 'with st.expander("Exact node arithmetic", expanded=False):' in SOURCE
    assert '"j-invariant = "' in SOURCE
    assert '"torsion invariants = "' in SOURCE
