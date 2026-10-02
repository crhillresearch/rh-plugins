"""Streamlit UI for the Symmetry Reducer feature plugin."""
from __future__ import annotations
import json
from pathlib import Path
import sys

try:
    import streamlit as st
except Exception:
    st = None

HERE = Path(__file__).resolve().parent

# Rank Hunter loads extension entrypoints as standalone modules.  Never import a
# sibling backend with a generic name such as ``engine``: another extension may
# already have populated sys.modules["engine"].  Load this backend under a
# plugin-unique module name instead.
def _load_local_engine():
    import importlib.util

    module_name = "rank42_extension_torsion_symmetry_reducer_engine"
    module = sys.modules.get(module_name)
    if module is not None:
        return module

    path = HERE / "engine.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load Torsion Symmetry backend: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_engine = _load_local_engine()
SymmetryError = _engine.SymmetryError
audit_weierstrass_2torsion = _engine.audit_weierstrass_2torsion
chart_audit_from_payload = _engine.chart_audit_from_payload
recover_pgl2_from_samples = _engine.recover_pgl2_from_samples


def _bytes(v):
    return (json.dumps(v, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _load_upload(upload):
    return json.loads(upload.getvalue().decode("utf-8"))


def render(context):
    if st is None:
        raise RuntimeError("Torsion Symmetry Reducer UI requires Streamlit")

    st.title("Symmetry Reducer")
    st.info(
        "Exact search-space symmetry tool, not a rank heuristic. When this feature plugin is enabled, "
        "validated family-search hooks may transparently remove proven duplicate chart searches before launch. "
        "The torsion/PGL₂ audit tools remain available below."
    )

    tab_runtime, tab_audit, tab_recover, tab_reduce, tab_schema = st.tabs([
        "Runtime Feature", "2-Torsion Audit", "Recover Native Action", "Chart Orbit Reducer", "Schemas / Boundary"
    ])

    with tab_runtime:
        st.subheader("Automatic family-search hook")
        st.success("Enabled feature plugins can now transform adapter-built search commands through the Rank Hunter core hook.")
        st.markdown(
            """
**Runtime scope**

- **Campbell 1999** PGL₂ family/target searches: A/B validated.
- **Mestre/Fermigier** PGL₂ searches: supported; rational mode can use the full source-height orbit, while integer/both use sign only.
- **Kihara 2001** Möbius chart searches: supported through the shared `rank_charts()` planner; rational source-height symmetry only.
- `dedup` is the conservative default. Start Rank Hunter with `RANK42_SYMMETRY_PLAN_MODE=refill` to generate farther down the ranking until the requested number of distinct chart-orbit representatives is reached.
- Reciprocal reduction is guarded by the affine-infinity boundary test.
- No family plugin is edited; disabling this Feature restores the original adapter command.

Campbell has passed real A/B native-fibre preservation controls. Mestre and Kihara support is ready for the same A/B validation before refill mode is treated as production-validated. This feature never upgrades rank evidence.
            """
        )

    with tab_audit:
        st.subheader("Automatic Weierstrass-x audit")
        st.write(
            "For `y² = x³ + a₂x² + a₄x + a₆`, every rational root `r` gives the 2-torsion point `(r,0)`. "
            "The induced translation on this same x-coordinate is computed exactly as a Möbius transformation."
        )
        c1,c2,c3 = st.columns(3)
        a2 = c1.text_input("a₂", "0", key="ts-a2")
        a4 = c2.text_input("a₄", "-1", key="ts-a4")
        a6 = c3.text_input("a₆", "0", key="ts-a6")
        if st.button("Audit rational 2-torsion", key="ts-audit-btn"):
            try:
                report = audit_weierstrass_2torsion({"a2":a2,"a4":a4,"a6":a6})
                st.session_state["ts-audit-report"] = report
            except Exception as exc:
                st.error(str(exc))
        report = st.session_state.get("ts-audit-report")
        if report:
            m1,m2 = st.columns(2)
            m1.metric("Nonzero rational 2-torsion", report["rational_nonzero_2torsion_points"])
            m2.metric("PGL₂ action group order", report["generated_action_group_order"])
            if report["actions"]:
                st.dataframe([
                    {"T x-coordinate":a["torsion_x"], "PGL2 matrix":a["pgl2_matrix"], "Action":a["formula"]}
                    for a in report["actions"]
                ], hide_index=True, width="stretch")
            else:
                st.warning("No rational 2-torsion found in this cubic model.")
            st.download_button("Export exact action group", _bytes(report), "torsion-pgl2-actions.json", "application/json")
            st.caption(report["claim_boundary"])

    with tab_recover:
        st.subheader("Recover the action in the coordinate we actually search")
        st.write(
            "This is the important mode for native quartics. Upload at least three exact pairs `x → x_after_T` "
            "coming from the *same* torsion translation. The tool solves for the unique PGL₂ map and verifies every supplied pair."
        )
        template = {"samples":[
            {"x":"0", "image":"1"},
            {"x":"1", "image":"0"},
            {"x":"2", "image":"-1"}
        ]}
        st.download_button("Download sample template", _bytes(template), "torsion-action-samples-template.json", "application/json")
        up = st.file_uploader("Exact native-coordinate samples JSON", type=["json"], key="ts-samples")
        if up:
            try:
                data = _load_upload(up)
                samples = data.get("samples") if isinstance(data,dict) else data
                recovered = recover_pgl2_from_samples(samples)
                st.success(f"Recovered and verified exact PGL₂ action from {recovered['samples_verified']} samples.")
                st.code(str(recovered["pgl2_matrix"]))
                st.download_button("Export recovered action", _bytes(recovered), "torsion-native-action.json", "application/json")
                st.caption(recovered["claim_boundary"])
            except Exception as exc:
                st.error(f"Recovery failed: {exc}")

    with tab_reduce:
        st.subheader("How many chart searches are duplicates?")
        st.write(
            "Upload a Rank-Hunter-style chart list and exact PGL₂ action group acting on that same native x-coordinate. "
            "Charts use `x=(A z+B)/(C z+D)`. The reducer groups `M` and `g∘M` into one torsion orbit."
        )
        cu = st.file_uploader("Charts JSON", type=["json"], key="ts-charts")
        au = st.file_uploader("Exact action/group JSON", type=["json"], key="ts-actions")
        coord = st.text_input("Coordinate label", "native quartic x", key="ts-coordinate")
        if cu and au:
            try:
                result = chart_audit_from_payload(_load_upload(cu), _load_upload(au), coordinate_label=coord)
                a,b,c,d = st.columns(4)
                a.metric("Input charts", result["input_charts"])
                b.metric("Unique torsion orbits", result["unique_chart_orbits"])
                c.metric("Searches saved", result["searches_saved_if_one_per_observed_orbit"])
                d.metric("Savings", f"{result['savings_percent']:.1f}%")
                if result["searches_saved_if_one_per_observed_orbit"]:
                    st.success(
                        f"Exact chart-orbit result: {result['input_charts']} supplied charts collapse to "
                        f"{result['unique_chart_orbits']} torsion-distinct searches (×{result['dedup_factor']:.2f} redundancy)."
                    )
                else:
                    st.info("No duplicate charts under the supplied torsion action were present in this chart set.")
                st.dataframe([
                    {"Orbit":o["orbit"], "Representative":o["representative_chart_id"],
                     "Observed charts":o["observed_members"], "Full orbit":o["full_group_orbit_size"],
                     "Members":", ".join(o["member_chart_ids"])}
                    for o in result["orbits"]
                ], hide_index=True, width="stretch")
                st.download_button("Export one representative per orbit", _bytes({"charts":result["representatives"], "audit":{k:v for k,v in result.items() if k not in {"representatives"}}}), "torsion-distinct-charts.json", "application/json")
                st.download_button("Export full orbit audit", _bytes(result), "torsion-chart-orbit-audit.json", "application/json")
                st.caption(result["claim_boundary"])
            except Exception as exc:
                st.error(f"Chart audit failed: {exc}")

    with tab_schema:
        st.subheader("Scientific boundary")
        st.markdown(
            """
- **Exact:** rational arithmetic, PGL₂ matrices, group closure, chart-orbit membership.
- **Exact only in the stated coordinate:** a Weierstrass-x action must not be silently reused on a native quartic x-coordinate.
- **Native quartic mode:** recover/derive the torsion action in that native degree-2 coordinate first, then audit charts.
- **Search consequence:** one representative per proven orbit may avoid duplicated coordinate searches.
- **No rank claim:** torsion symmetry reduction does not prove extra points, independence, or rank growth.
            """
        )
        st.write("Reference idea: equivariant degree-2 morphisms and torsion-induced PGL₂ actions from Faugère–Huot–Joux–Renault–Vitse (EUROCRYPT 2014).")
