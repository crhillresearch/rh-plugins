from __future__ import annotations

import html
import importlib.util
import math
import sys
from pathlib import Path

import streamlit as st


def _load_local_module(filename: str, module_name: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


try:
    from rank42.ui_handoffs import (
        normalize_research_handoff,
        route_curve_to_target,
        route_selection_to_pipelines,
    )
    HANDOFF_OWNER = "core"
except ModuleNotFoundError as exc:
    if exc.name != "rank42.ui_handoffs":
        raise
    _HANDOFFS = _load_local_module(
        "handoff_compat.py",
        "rank42_fiber_atlas_handoff_compat",
    )
    normalize_research_handoff = _HANDOFFS.normalize_research_handoff
    route_curve_to_target = _HANDOFFS.route_curve_to_target
    route_selection_to_pipelines = _HANDOFFS.route_selection_to_pipelines
    HANDOFF_OWNER = "compat"


def _load_backend():
    path = Path(__file__).with_name("backend.py")
    spec = importlib.util.spec_from_file_location("rank42_fiber_atlas_backend", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = _load_backend()


def _nice_step(span: float, target: int = 6) -> float:
    raw = max(float(span) / max(int(target), 1), 1e-12)
    power = 10 ** math.floor(math.log10(raw))
    ratio = raw / power
    if ratio < 1.5:
        return power
    if ratio < 3.5:
        return 2 * power
    if ratio < 7.5:
        return 5 * power
    return 10 * power


def _bounds(values):
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return (-1.0, 1.0)
    lo, hi = values[0], values[-1]
    if lo == hi:
        pad = max(1.0, abs(lo) * 0.12)
        return lo - pad, hi + pad

    if len(values) >= 20:
        qlo = values[max(0, int(len(values) * 0.02) - 1)]
        qhi = values[min(len(values) - 1, int(len(values) * 0.98))]
        if qhi > qlo:
            lo, hi = qlo, qhi
    pad = max((hi - lo) * 0.07, 1e-9)
    return lo - pad, hi + pad


def _color_style(record, color_metric: str, score_range=None):
    if color_metric == "rank_jump":
        jump = record.rank_jump
        if jump is None:
            return "var(--rh-muted)", 0.38
        if jump >= 2:
            return "var(--rh-warning)", 0.98
        if jump == 1:
            return "var(--rh-success)", 0.96
        return "var(--rh-primary)", 0.68

    if color_metric == "rigorous_lower":
        lower = record.rigorous_lower
        if lower is None:
            return "var(--rh-muted)", 0.35
        return "var(--rh-primary)", min(1.0, 0.42 + 0.045 * max(0, lower))

    if color_metric == "score":
        if record.score is None:
            return "var(--rh-muted)", 0.35
        lo, hi = score_range or (record.score, record.score)
        ratio = 0.5 if not hi > lo else (record.score - lo) / (hi - lo)
        return "var(--rh-primary)", 0.30 + 0.68 * max(0.0, min(1.0, ratio))

    if color_metric == "root_number":
        if record.root_number == -1:
            return "var(--rh-warning)", 0.94
        if record.root_number == 1:
            return "var(--rh-primary)", 0.86
        return "var(--rh-muted)", 0.34

    if color_metric == "exact_rank":
        if record.exact_known:
            return "var(--rh-success)", 0.98
        return "var(--rh-primary)", 0.58

    return "var(--rh-primary)", 0.80


def _legend_html(color_metric: str):
    if color_metric == "rank_jump":
        items = [
            ("var(--rh-primary)", "family baseline"),
            ("var(--rh-success)", "+1 above baseline"),
            ("var(--rh-warning)", "≥+2 above baseline"),
            ("var(--rh-muted)", "baseline unknown"),
        ]
    elif color_metric == "root_number":
        items = [
            ("var(--rh-warning)", "root number −1"),
            ("var(--rh-primary)", "root number +1"),
            ("var(--rh-muted)", "unknown"),
        ]
    elif color_metric == "exact_rank":
        items = [
            ("var(--rh-success)", "exact rank stored"),
            ("var(--rh-primary)", "lower bound only"),
        ]
    elif color_metric == "score":
        items = [
            ("var(--rh-primary)", "opacity increases with Nagao score"),
            ("var(--rh-muted)", "score unavailable"),
        ]
    else:
        items = [
            ("var(--rh-primary)", "opacity increases with rigorous lower"),
            ("var(--rh-muted)", "rank evidence unavailable"),
        ]
    return "".join(
        f'<span><i style="background:{color}"></i>{html.escape(label)}</span>'
        for color, label in items
    )


def _hover_text(record) -> str:
    lower = record.rigorous_lower
    jump = record.rank_jump
    exact = (
        f"exact rank {record.exact_rank}"
        if record.exact_rank is not None
        else "exact rank unknown"
    )
    root = (
        f"root {record.root_number:+d}"
        if record.root_number in (-1, 1)
        else "root unknown"
    )
    p = record.rational_parameter
    geometry = (
        f"num={p.numerator}, den={p.denominator}, logH={p.log_height:.3f}"
        if p is not None
        else "non-rational/unsupported parameter text"
    )
    score = f"{record.score:.3f}" if record.score is not None else "unavailable"
    bad = ",".join(str(x) for x in record.bad_primes) if record.bad_primes else "unknown"
    baseline_symbol = (
        "=" if record.baseline_is_exact else "≥"
    ) if record.family_baseline is not None else "?"
    excess_label = "rank jump" if record.baseline_is_exact else "baseline excess"
    return (
        f"curve #{record.curve_id} · t={record.parameter} · "
        f"rigorous lower {lower if lower is not None else '?'} · "
        f"row generic lower {record.generic_lower if record.generic_lower is not None else '?'} · "
        f"family baseline {baseline_symbol}{record.family_baseline if record.family_baseline is not None else '?'} · "
        f"{excess_label} {jump if jump is not None else '?'} · Nagao {score} · "
        f"{root} · {exact} · {geometry} · bad primes {bad} · "
        f"exact discoveries {record.exact_discoveries} · "
        f"quartic hits {record.quartic_hits} · "
        f"covering mapped {record.covering_mapped_points}"
    )


def _chart_html(plotted, x_metric: str, y_metric: str, color_metric: str) -> str:
    if not plotted:
        return """
        <div class="fa-empty">
          No stored fibers have both selected axis values after the current filters.
        </div>
        """

    W, H = 1160, 640
    L, R, T, BOT = 92, 30, 28, 70
    plot_w, plot_h = W - L - R, H - T - BOT
    xs = [x for _, x, _ in plotted]
    ys = [y for _, _, y in plotted]
    xmin, xmax = _bounds(xs)
    ymin, ymax = _bounds(ys)

    def X(value):
        return L + ((value - xmin) / (xmax - xmin)) * plot_w

    def Y(value):
        return T + plot_h - ((value - ymin) / (ymax - ymin)) * plot_h

    grid = []
    xstep = _nice_step(xmax - xmin, 7)
    x = math.ceil(xmin / xstep) * xstep
    guard = 0
    while x <= xmax + xstep * 1e-8 and guard < 24:
        px = X(x)
        grid.append(
            f'<line x1="{px:.1f}" y1="{T}" x2="{px:.1f}" y2="{T + plot_h}" '
            'stroke="var(--rh-border)" stroke-width="1"/>'
        )
        grid.append(
            f'<text x="{px:.1f}" y="{T + plot_h + 27}" text-anchor="middle" '
            'fill="var(--rh-muted)" font-size="12" font-family="Inter,system-ui,sans-serif">'
            f'{x:.3g}</text>'
        )
        x += xstep
        guard += 1

    ystep = _nice_step(ymax - ymin, 6)
    y = math.ceil(ymin / ystep) * ystep
    guard = 0
    while y <= ymax + ystep * 1e-8 and guard < 24:
        py = Y(y)
        grid.append(
            f'<line x1="{L}" y1="{py:.1f}" x2="{W - R}" y2="{py:.1f}" '
            'stroke="var(--rh-border)" stroke-width="1"/>'
        )
        grid.append(
            f'<text x="{L - 12}" y="{py + 4:.1f}" text-anchor="end" '
            'fill="var(--rh-muted)" font-size="12" font-family="Inter,system-ui,sans-serif">'
            f'{y:.3g}</text>'
        )
        y += ystep
        guard += 1

    scores = [record.score for record, _, _ in plotted if record.score is not None]
    score_range = (min(scores), max(scores)) if scores else (0.0, 0.0)

    dots = []
    for record, xvalue, yvalue in plotted:
        px = X(min(xmax, max(xmin, xvalue)))
        py = Y(min(ymax, max(ymin, yvalue)))
        color, opacity = _color_style(record, color_metric, score_range)
        title = html.escape(_hover_text(record), quote=False)
        radius = 5.3 + min(4.5, max(0, (record.rank_jump or 0)) * 1.35)
        dots.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{radius:.1f}" '
            f'fill="{color}" fill-opacity="{opacity:.2f}" '
            f'stroke="{color}" stroke-opacity="1" stroke-width="1.2">'
            f'<title>{title}</title></circle>'
        )

    xaxis = html.escape(B.PLOT_METRICS[x_metric]["axis"])
    yaxis = html.escape(B.PLOT_METRICS[y_metric]["axis"])
    legend = _legend_html(color_metric)

    return f"""
    <div class="fa-chart-shell">
      <div class="fa-legend">{legend}</div>
      <svg viewBox="0 0 {W} {H}" role="img"
           aria-label="Fiber Atlas parameter-space landscape">
        {''.join(grid)}
        <line x1="{L}" y1="{T}" x2="{L}" y2="{T + plot_h}"
              stroke="var(--rh-muted-2)" stroke-width="1.5"/>
        <line x1="{L}" y1="{T + plot_h}" x2="{W - R}" y2="{T + plot_h}"
              stroke="var(--rh-muted-2)" stroke-width="1.5"/>
        <text x="{L + plot_w / 2:.1f}" y="{H - 15}" text-anchor="middle"
              fill="var(--rh-text-secondary)" font-size="14"
              font-family="Inter,system-ui,sans-serif">{xaxis} →</text>
        <text transform="rotate(-90)" x="{- (T + plot_h / 2):.1f}" y="25"
              text-anchor="middle" fill="var(--rh-text-secondary)"
              font-size="14" font-family="Inter,system-ui,sans-serif">{yaxis}</text>
        {''.join(dots)}
      </svg>
    </div>
    """


def _range_slider(label, values, *, key, integer=False):
    values = [value for value in values if value is not None]
    if not values:
        st.caption(f"{label}: unavailable")
        return (None, None)
    lo, hi = min(values), max(values)
    if lo == hi:
        st.caption(f"{label}: {lo:.3f}" if not integer else f"{label}: {int(lo)}")
        return (None, None)
    if integer:
        full = (int(lo), int(hi))
        selected = st.slider(
            label,
            min_value=full[0],
            max_value=full[1],
            value=full,
            step=1,
            key=key,
        )
    else:
        full = (float(lo), float(hi))
        selected = st.slider(
            label,
            min_value=full[0],
            max_value=full[1],
            value=full,
            key=key,
        )
    # An untouched full-range control is not a scientific filter. Keeping it
    # as None also means rows with unknown lower/parameter metadata stay visible
    # in modes that do not require that field.
    return (None, None) if tuple(selected) == full else tuple(selected)


def _filters(records):
    with st.expander("Filters", expanded=False):
        row1 = st.columns([0.9, 1.15, 1.45])
        with row1[0]:
            root_filter = st.selectbox(
                "Root number",
                ["Any", "-1", "+1", "Unknown"],
                key="fiber-atlas-filter-root",
            )
        with row1[1]:
            exact_filter = st.selectbox(
                "Rank status",
                ["Any", "Exact rank stored", "Lower bound only"],
                key="fiber-atlas-filter-exact",
            )
        with row1[2]:
            lowers = [
                record.rigorous_lower
                for record in records
                if record.rigorous_lower is not None
            ]
            lower_min, lower_max = _range_slider(
                "Rigorous lower band",
                lowers,
                key="fiber-atlas-filter-lower",
                integer=True,
            )

        rational = [
            record.rational_parameter
            for record in records
            if record.rational_parameter is not None
        ]
        row2 = st.columns(2)
        with row2[0]:
            height_min, height_max = _range_slider(
                "log rational height band",
                [p.log_height for p in rational],
                key="fiber-atlas-filter-height",
            )
        with row2[1]:
            den_min, den_max = _range_slider(
                "log denominator band",
                [p.log_denominator for p in rational],
                key="fiber-atlas-filter-denominator",
            )

    filtered = B.filter_records(
        records,
        root_filter=root_filter,
        exact_filter=exact_filter,
        lower_min=lower_min,
        lower_max=lower_max,
        log_height_min=height_min,
        log_height_max=height_max,
        log_denominator_min=den_min,
        log_denominator_max=den_max,
    )
    filter_spec = {
        "root_number": None if root_filter == "Any" else root_filter,
        "rank_status": None if exact_filter == "Any" else exact_filter,
        "rigorous_lower": (
            None
            if lower_min is None and lower_max is None
            else [lower_min, lower_max]
        ),
        "log_height": (
            None
            if height_min is None and height_max is None
            else [height_min, height_max]
        ),
        "log_denominator": (
            None
            if den_min is None and den_max is None
            else [den_min, den_max]
        ),
    }
    return filtered, {
        key: value
        for key, value in filter_spec.items()
        if value is not None
    }


def _mode_controls(view: str):
    if view == "Landscape":
        controls = st.columns([1.15, 1.15, 1.0])
        metric_keys = [
            "log_height",
            "log_denominator",
            "signed_log_numerator",
            "parameter",
            "score",
            "rigorous_lower",
            "rank_jump",
            "root_number",
        ]
        with controls[0]:
            x_metric = st.selectbox(
                "X axis",
                metric_keys,
                index=metric_keys.index("log_height"),
                format_func=lambda key: B.PLOT_METRICS[key]["label"],
                key="fiber-atlas-landscape-x",
            )
        with controls[1]:
            y_metric = st.selectbox(
                "Y axis",
                metric_keys,
                index=metric_keys.index("score"),
                format_func=lambda key: B.PLOT_METRICS[key]["label"],
                key="fiber-atlas-landscape-y",
            )
        with controls[2]:
            color_metric = st.selectbox(
                "Color",
                list(B.COLOR_METRICS),
                index=list(B.COLOR_METRICS).index("rank_jump"),
                format_func=lambda key: B.COLOR_METRICS[key],
                key="fiber-atlas-landscape-color",
            )
        return x_metric, y_metric, color_metric

    if view == "Farey / denominator":
        controls = st.columns([1.2, 1.0])
        with controls[0]:
            st.caption(
                "Rational numerator/denominator geometry. This is not a Farey adjacency graph; "
                "it is a coordinate view of where tested rational parameters concentrate."
            )
        with controls[1]:
            color_metric = st.selectbox(
                "Color",
                list(B.COLOR_METRICS),
                index=list(B.COLOR_METRICS).index("root_number"),
                format_func=lambda key: B.COLOR_METRICS[key],
                key="fiber-atlas-farey-color",
            )
        return "signed_log_numerator", "log_denominator", color_metric

    if view == "Rank jumps":
        controls = st.columns([1.2, 1.0])
        x_options = ["log_height", "score", "log_denominator", "parameter"]
        with controls[0]:
            x_metric = st.selectbox(
                "X axis",
                x_options,
                index=0,
                format_func=lambda key: B.PLOT_METRICS[key]["label"],
                key="fiber-atlas-jumps-x",
            )
        with controls[1]:
            color_metric = st.selectbox(
                "Color",
                list(B.COLOR_METRICS),
                index=list(B.COLOR_METRICS).index("rigorous_lower"),
                format_func=lambda key: B.COLOR_METRICS[key],
                key="fiber-atlas-jumps-color",
            )
        return x_metric, "rank_jump", color_metric

    controls = st.columns([1.1, 1.2, 1.0])
    x_options = ["log_height", "score", "log_denominator", "parameter"]
    with controls[0]:
        x_metric = st.selectbox(
            "X axis",
            x_options,
            index=0,
            format_func=lambda key: B.PLOT_METRICS[key]["label"],
            key="fiber-atlas-yield-x",
        )
    with controls[1]:
        y_metric = st.selectbox(
            "Yield measure",
            list(B.SEARCH_YIELD_METRICS),
            index=0,
            format_func=lambda key: B.SEARCH_YIELD_METRICS[key],
            key="fiber-atlas-yield-y",
        )
    with controls[2]:
        color_metric = st.selectbox(
            "Color",
            list(B.COLOR_METRICS),
            index=list(B.COLOR_METRICS).index("rank_jump"),
            format_func=lambda key: B.COLOR_METRICS[key],
            key="fiber-atlas-yield-color",
        )
    return x_metric, y_metric, color_metric


def _yield_cards(records):
    summary = B.yield_summary(records)
    cols = st.columns(4)
    cols[0].metric("Exact discoveries", f"{summary['exact_discoveries']:,}")
    cols[1].metric("Quartic hits", f"{summary['quartic_hits']:,}")
    cols[2].metric("Covering mapped", f"{summary['covering_mapped_points']:,}")
    cols[3].metric("Rigorous point witnesses", f"{summary['rigorous_points']:,}")
    st.caption(
        "Search-yield counts are durable stored artifacts/events. They describe where previous "
        "search work produced objects; they are not a rank predictor or proof by themselves."
    )


def _prime_fingerprint(records, *, db, family):
    with st.expander("Bad-prime fingerprint", expanded=False):
        cache_key = f"fiber-atlas-prime-cache::{family}"
        prime_cache = st.session_state.get(cache_key)
        if prime_cache is None:
            st.caption(
                "Bad-prime metadata is intentionally lazy on large databases. "
                "Load it only when you want this fingerprint."
            )
            if not st.button(
                "Load bad-prime fingerprint",
                key="fiber-atlas-load-bad-primes",
            ):
                return
            with st.spinner("Loading stored bad-prime metadata…"):
                prime_cache = B.load_bad_prime_signals(db, family)
            st.session_state[cache_key] = prime_cache
            st.rerun()

        enriched = B.apply_bad_prime_signals(records, prime_cache)
        rows = B.bad_prime_fingerprint(enriched)
        if not rows:
            st.caption("No exact stored bad-prime metadata is available for the current fibers.")
            return
        metadata_fibers = int(rows[0]["metadata_fibers"])
        st.caption(
            f"Exact stored bad-prime incidence across {metadata_fibers:,} filtered fiber"
            f"{'s' if metadata_fibers != 1 else ''}. Frequency is descriptive only."
        )
        st.dataframe(
            [
                {
                    "prime": int(row["prime"]),
                    "fibers": int(row["fibers"]),
                    "share of fibers with bad-prime metadata": f"{100.0 * float(row['share']):.1f}%",
                }
                for row in rows
            ],
            hide_index=True,
            width="stretch",
        )


def _row(record):
    p = record.rational_parameter
    return {
        "curve": record.curve_id,
        "parameter": B.parameter_display(record),
        "numerator": p.numerator if p is not None else None,
        "denominator": p.denominator if p is not None else None,
        "log H": round(p.log_height, 4) if p is not None else None,
        "Nagao": round(record.score, 4) if record.score is not None else None,
        "root": record.root_number if record.root_number in (-1, 1) else None,
        "bad primes": ",".join(str(x) for x in record.bad_primes) or None,
        "row generic lower": record.generic_lower,
        "family baseline": record.family_baseline,
        "baseline status": (
            "exact generic rank"
            if record.baseline_is_exact
            else "generic lower bound"
            if record.family_baseline is not None
            else None
        ),
        "rigorous lower": record.rigorous_lower,
        "rank jump / excess": record.rank_jump,
        "exact rank": record.exact_rank,
        "exact discoveries": record.exact_discoveries,
        "quartic hits": record.quartic_hits,
        "covering mapped": record.covering_mapped_points,
        "rigorous points": record.rigorous_points,
    }


MAX_HANDOFF_FIBERS = 250


def _selection_panel(
    records,
    *,
    family,
    view,
    x_metric,
    y_metric,
    color_metric,
    filters,
):
    ordered = B.picker_order(records)
    with st.expander("Selection & handoff", expanded=False):
        st.caption(
            "Turn the current visual hypothesis into an explicit Rank Hunter handoff. "
            "Fiber Atlas still executes nothing itself."
        )
        mode = st.radio(
            "Selection source",
            ["Current filtered region", "Chosen fibers"],
            horizontal=True,
            key="fiber-atlas-selection-mode",
        )

        labels = {
            record.curve_id: (
                f"curve #{record.curve_id} · t={B.parameter_display(record)} · "
                f"rigorous ≥{record.rigorous_lower if record.rigorous_lower is not None else '?'} · "
                f"{'jump' if record.baseline_is_exact else 'excess'} "
                f"{record.rank_jump if record.rank_jump is not None else '?'}"
            )
            for record in ordered
        }

        if mode == "Chosen fibers":
            selectable = ordered[:1000]
            chosen_ids = st.multiselect(
                "Stored fibers",
                [record.curve_id for record in selectable],
                default=[],
                format_func=lambda curve_id: labels[int(curve_id)],
                key="fiber-atlas-selection-fibers",
                help=(
                    "The chooser is capped to the first 1,000 filtered fibers by "
                    "Fiber Atlas priority. Narrow the filters to expose a different region."
                ),
            )
            chosen = {int(curve_id) for curve_id in chosen_ids}
            selected_records = [
                record for record in ordered if record.curve_id in chosen
            ]
        else:
            selected_records = ordered

        if not selected_records:
            st.caption("No fibers are currently selected.")
            return

        if len(selected_records) > MAX_HANDOFF_FIBERS:
            st.warning(
                f"This region contains {len(selected_records):,} fibers. "
                f"Narrow the Atlas filters to at most {MAX_HANDOFF_FIBERS:,} "
                "before handing it off so the selection remains explicit and inspectable."
            )
            return

        payload = B.selection_payload(
            selected_records,
            family=family,
            view=view,
            x_metric=x_metric,
            y_metric=y_metric,
            color_metric=color_metric,
            filters=filters,
        )
        normalized = normalize_research_handoff(payload)

        summary_cols = st.columns(3)
        summary_cols[0].metric("Selected fibers", f"{len(selected_records):,}")
        summary_cols[1].metric(
            "Max rigorous lower",
            max(
                (
                    record.rigorous_lower
                    for record in selected_records
                    if record.rigorous_lower is not None
                ),
                default="—",
            ),
        )
        summary_cols[2].metric(
            "Selection hash",
            normalized["selection_hash"][:12],
        )

        primary_id = st.selectbox(
            "Primary fiber",
            [record.curve_id for record in selected_records],
            format_func=lambda curve_id: labels[int(curve_id)],
            key="fiber-atlas-selection-primary",
            help=(
                "Target Search attacks one stored specialization. The full selection "
                "travels with it as research provenance."
            ),
        )
        primary = next(
            record
            for record in selected_records
            if record.curve_id == int(primary_id)
        )

        a, b, d = st.columns(3)
        with a:
            if st.button(
                "Open curve",
                width="stretch",
                key="fiber-atlas-handoff-curve",
            ):
                _open_curve(primary)
        with b:
            if st.button(
                "Target Search",
                type="primary",
                width="stretch",
                key="fiber-atlas-handoff-target",
            ):
                route_curve_to_target(
                    st.session_state,
                    primary.curve_id,
                    handoff=payload,
                )
                st.rerun()
        with d:
            if st.button(
                "Pipelines",
                width="stretch",
                key="fiber-atlas-handoff-pipelines",
                help=(
                    "Carries the explicit region into Pipelines as context. "
                    "It does not change Builder modules or candidate sources."
                ),
            ):
                route_selection_to_pipelines(st.session_state, payload)
                st.rerun()

        with st.expander("Inspect handoff", expanded=False):
            st.json(normalized)
            st.caption(
                "The SHA-256 selection hash is computed from the normalized family, "
                "curve IDs, parameters, view, axes, filters, and parameter envelope. "
                "Repeating the same selection produces the same hash."
            )


def _open_curve(record):
    st.session_state["curves_selected_id"] = int(record.curve_id)
    st.session_state["curves-filter"] = ""
    st.session_state["curves-minrank"] = 0
    st.session_state["curves-family"] = "All"
    st.session_state["curves-evidence"] = "Any"
    st.session_state["curves-status"] = "Any"
    st.session_state["rh_page"] = "Curves"
    st.rerun()


def render(context):
    st.markdown(
        """
        <style>
        .fa-science-note{
            color:var(--rh-muted);font-size:.86rem;margin:.15rem 0 .75rem 0
        }
        .fa-chart-shell{
            background:var(--rh-card);border:1px solid var(--rh-border);
            border-radius:16px;padding:13px 14px 4px 14px;
            box-shadow:0 12px 36px color-mix(in srgb,var(--rh-text) 10%,transparent);
            overflow:hidden
        }
        .fa-chart-shell svg{display:block;width:100%;height:auto}
        .fa-legend{
            display:flex;gap:14px;align-items:center;flex-wrap:wrap;
            padding:2px 8px 7px 8px;color:var(--rh-text-secondary);
            font:600 11px Inter,system-ui,sans-serif
        }
        .fa-legend span{display:inline-flex;gap:6px;align-items:center}
        .fa-legend i{width:9px;height:9px;border-radius:50%;display:inline-block}
        .fa-empty{
            background:var(--rh-card);border:1px solid var(--rh-border);
            border-radius:16px;color:var(--rh-muted);padding:34px 22px;text-align:center
        }
        .fa-post-chart-gap{height:1rem}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Explore where stored specializations live in a family's rational parameter space. "
        "Fiber Atlas is read-only: visual clusters, Nagao scores, root-number patterns, bad-prime "
        "fingerprints, search-yield patterns, and baseline-excess neighborhoods are research/scheduling "
        "signals, not proofs."
    )

    inventory = B.list_families(context.db)
    if not inventory:
        st.info("No stored curve families are available yet.")
        return

    by_family = {item.family: item for item in inventory}
    preferred_family = st.session_state.get("curves-family")
    index = next(
        (
            i for i, item in enumerate(inventory)
            if preferred_family and item.family == preferred_family
        ),
        0,
    )
    family = st.selectbox(
        "Family",
        [item.family for item in inventory],
        index=index,
        format_func=lambda name: (
            f"{name} · {by_family[name].count:,} stored fiber"
            f"{'s' if by_family[name].count != 1 else ''}"
        ),
        key="fiber-atlas-family",
    )

    records = B.load_family(
        context.db,
        family,
        project_root=getattr(context, "project_root", Path.cwd()),
    )
    prime_cache = st.session_state.get(f"fiber-atlas-prime-cache::{family}")
    if prime_cache is not None:
        records = B.apply_bad_prime_signals(records, prime_cache)
    summary = B.family_summary(records)

    baseline = summary.get("family_baseline")
    baseline_kind = summary.get("family_baseline_kind")
    baseline_source = summary.get("family_baseline_source")
    baseline_detail = summary.get("family_baseline_detail")
    baseline_exact = baseline_kind == "exact_generic_rank"
    baseline_display = (
        ("=" if baseline_exact else "≥") + str(int(baseline))
        if baseline is not None
        else "—"
    )
    excess_label = "Rank-jump fibers" if baseline_exact else "Baseline-excess fibers"
    max_excess_label = "Max rank jump" if baseline_exact else "Max baseline excess"

    cards = st.columns(6)
    cards[0].metric("Stored fibers", f"{summary['fibers']:,}")
    cards[1].metric("Family baseline", baseline_display)
    cards[2].metric(
        "Max rigorous lower",
        "—" if summary["max_rigorous_lower"] is None else summary["max_rigorous_lower"],
    )
    cards[3].metric(excess_label, f"{summary['baseline_excess_fibers']:,}")
    cards[4].metric(
        max_excess_label,
        "—"
        if summary["max_baseline_excess"] is None
        else f"+{summary['max_baseline_excess']}",
    )
    cards[5].metric(
        "Max Nagao",
        "—" if summary["max_score"] is None else f"{summary['max_score']:.3f}",
    )

    rational_count = int(summary.get("rational_parameters") or 0)
    root_known = int(summary.get("root_number_known") or 0)
    source_text = baseline_detail or baseline_source or "unavailable"
    st.markdown(
        (
            f"<div class='fa-science-note'>"
            f"Rational parameter geometry available for {rational_count:,}/{len(records):,} fibers"
            f" · stored root number available for {root_known:,}/{len(records):,}"
            f" · exact ranks stored for {int(summary.get('exact_rank_fibers') or 0):,}"
            f" · family baseline source: {html.escape(str(source_text))}"
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
    if baseline is None:
        st.warning(
            "No authoritative family-level generic baseline is available. "
            "Fiber Atlas will not invent rank-jump values from specialization rows."
        )
    elif baseline_exact:
        st.caption(
            f"Generic rank is exact at {int(baseline)} from family-level evidence; "
            "differences above this baseline are genuine rigorous rank jumps."
        )
    else:
        st.caption(
            f"Recorded generic baseline is a rigorous lower bound ≥{int(baseline)}. "
            "Displayed differences are excess above that recorded lower bound; they are "
            "not by themselves proof of the jump above the unknown exact generic rank."
        )

    filtered, filter_spec = _filters(records)
    st.caption(
        f"Current filters retain {len(filtered):,} of {len(records):,} stored fibers."
    )

    views = ["Landscape", "Farey / denominator", "Rank jumps", "Search yield"]
    view = st.segmented_control(
        "Atlas view",
        views,
        default="Landscape",
        key="fiber-atlas-view",
        label_visibility="collapsed",
        width="stretch",
    ) or "Landscape"

    if view == "Rank jumps":
        if baseline is None:
            st.warning(
                "Rank-jump view needs an authoritative family baseline; none is available."
            )
        elif baseline_exact:
            st.caption(
                f"Rank-jump axis = specialization rigorous lower − exact generic rank {int(baseline)}."
            )
        else:
            st.caption(
                f"Baseline-excess axis = specialization rigorous lower − recorded generic lower "
                f"{int(baseline)}. This is proof-conservative excess, not an exact generic-rank jump."
            )

    if view == "Search yield":
        cache_key = f"fiber-atlas-yield-cache::{family}"
        signal_cache = st.session_state.get(cache_key)
        if signal_cache is None:
            st.info(
                "Search-yield history is intentionally lazy on large databases. "
                "Load it only when you want this view; ordinary family switching stays fast."
            )
            if not st.button(
                "Load search-yield history",
                key="fiber-atlas-load-yield",
                type="primary",
            ):
                return
            with st.spinner("Loading durable search-yield history…"):
                signal_cache = B.load_search_yield_signals(context.db, family)
            st.session_state[cache_key] = signal_cache
        filtered = B.apply_search_yield_signals(filtered, signal_cache)
        _yield_cards(filtered)

    x_metric, y_metric, color_metric = _mode_controls(view)
    raw_plotted = B.plottable_records(filtered, x_metric, y_metric)
    plotted = B.bound_plotted(raw_plotted, max_points=800)
    bounded = len(plotted) != len(raw_plotted)
    st.caption(
        f"Plotting {len(plotted):,} of {len(raw_plotted):,} plottable filtered fibers"
        + (
            " (bounded display preserves high-signal fibers plus a deterministic sample)."
            if bounded
            else ". Hover a point for exact stored parameter/evidence/search metadata."
        )
    )
    st.markdown(
        _chart_html(plotted, x_metric, y_metric, color_metric),
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='fa-post-chart-gap' aria-hidden='true'></div>",
        unsafe_allow_html=True,
    )

    _prime_fingerprint(
        filtered,
        db=context.db,
        family=family,
    )

    _selection_panel(
        filtered,
        family=family,
        view=view,
        x_metric=x_metric,
        y_metric=y_metric,
        color_metric=color_metric,
        filters=filter_spec,
    )

    st.markdown("#### Inspect a stored fiber")
    ordered = B.picker_order(filtered)
    if not ordered:
        st.caption("No stored fibers match the current filters.")
        return

    labels = {
        record.curve_id: (
            f"curve #{record.curve_id} · t={B.parameter_display(record)} · "
            f"rigorous ≥{record.rigorous_lower if record.rigorous_lower is not None else '?'} · "
            f"{'jump' if record.baseline_is_exact else 'excess'} "
            f"{record.rank_jump if record.rank_jump is not None else '?'} · "
            f"Nagao {record.score:.3f}"
            if record.score is not None
            else
            f"curve #{record.curve_id} · t={B.parameter_display(record)} · "
            f"rigorous ≥{record.rigorous_lower if record.rigorous_lower is not None else '?'} · "
            f"{'jump' if record.baseline_is_exact else 'excess'} "
            f"{record.rank_jump if record.rank_jump is not None else '?'} · Nagao —"
        )
        for record in ordered
    }
    selected_id = st.selectbox(
        "Fiber",
        [record.curve_id for record in ordered],
        format_func=lambda curve_id: labels[int(curve_id)],
        key="fiber-atlas-open-curve",
    )
    selected = next(record for record in ordered if record.curve_id == int(selected_id))

    button_col, note_col = st.columns([0.28, 0.72])
    with button_col:
        if st.button(
            "Open selected curve",
            type="primary",
            use_container_width=True,
            key="fiber-atlas-open-button",
        ):
            _open_curve(selected)
    with note_col:
        st.caption(
            "Opening a fiber hands off to the ordinary Curves page. "
            "Fiber Atlas does not execute searches or modify rank evidence."
        )

    with st.expander(f"Filtered family fibers ({len(ordered):,})", expanded=False):
        table_rows = ordered[:1000]
        if len(ordered) > len(table_rows):
            st.caption(
                f"Showing the first {len(table_rows):,} of {len(ordered):,} filtered fibers. "
                "Narrow the filters to inspect a smaller region."
            )
        st.dataframe(
            [_row(record) for record in table_rows],
            hide_index=True,
            width="stretch",
            height=min(560, max(160, 42 + 35 * min(len(table_rows), 13))),
        )
