from __future__ import annotations

import html
import importlib.util
import math
import sys
from pathlib import Path

import streamlit as st


def _load_backend():
    path = Path(__file__).with_name("backend.py")
    spec = importlib.util.spec_from_file_location("rank42_leaderboard_compare_backend", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = _load_backend()


def _fmt_metric(value: float | None, metric_key: str) -> str:
    if value is None:
        return "—"
    if metric_key in ("conductor", "disc"):
        return f"{value:.3f}"
    return f"{value:.4f}"


def _source_color(source: str) -> str:
    return "var(--rh-primary)" if source == B.LOCAL_SOURCE else "var(--rh-muted)"


def _source_opacity(source: str) -> float:
    return 0.96 if source == B.LOCAL_SOURCE else 0.46


def _nice_step(span: float, target: int = 6) -> float:
    raw = max(span / max(target, 1), 1e-12)
    power = 10 ** math.floor(math.log10(raw))
    ratio = raw / power
    if ratio < 1.5:
        return power
    if ratio < 3.5:
        return 2 * power
    if ratio < 7.5:
        return 5 * power
    return 10 * power


def _chart_html(points, metric_key: str, rank_min: int, rank_max: int) -> str:
    metric = B.METRICS[metric_key]
    values = [p.metric(metric_key) for p in points]
    values = [float(v) for v in values if v is not None]
    if not values:
        return """
        <div class="lb-empty">
          No plotted curves have this metric in the selected filters.
        </div>
        """

    W, H = 1120, 620
    L, R, T, BOT = 86, 28, 28, 64
    plot_w, plot_h = W - L - R, H - T - BOT
    qmin, qmax = min(values), max(values)
    if qmin == qmax:
        pad = max(1.0, abs(qmin) * 0.05)
        qmin -= pad
        qmax += pad
    else:
        pad = (qmax - qmin) * 0.07
        qmin -= pad
        qmax += pad

    xmin = rank_min - 0.55
    xmax = rank_max + 0.55
    if xmax <= xmin:
        xmax = xmin + 1.0

    def X(rank: int) -> float:
        return L + ((rank - xmin) / (xmax - xmin)) * plot_w

    def Y(value: float) -> float:
        return T + plot_h - ((value - qmin) / (qmax - qmin)) * plot_h

    grid = []
    rank_span = max(1, rank_max - rank_min + 1)
    label_every = 1 if rank_span <= 13 else max(2, math.ceil(rank_span / 11))
    for rank in range(rank_min, rank_max + 1):
        x = X(rank)
        labeled = ((rank - rank_min) % label_every == 0) or rank in (rank_min, rank_max)
        if labeled:
            grid.append(
                f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{T + plot_h}" '
                'stroke="var(--rh-border)" stroke-width="1"/>'
            )
            grid.append(
                f'<text x="{x:.1f}" y="{T + plot_h + 26}" text-anchor="middle" '
                'fill="var(--rh-muted)" font-size="13" font-family="Inter,system-ui,sans-serif">'
                f'{rank}</text>'
            )
        tick_len = 9 if labeled else 14
        grid.append(
            f'<line x1="{x:.1f}" y1="{T + plot_h}" x2="{x:.1f}" '
            f'y2="{T + plot_h + tick_len}" stroke="var(--rh-muted-2)" stroke-width="1"/>'
        )

    ystep = _nice_step(qmax - qmin, 6)
    first = math.ceil(qmin / ystep) * ystep
    q = first
    guard = 0
    while q <= qmax + ystep * 1e-8 and guard < 20:
        y = Y(q)
        grid.append(
            f'<line x1="{L}" y1="{y:.1f}" x2="{W - R}" y2="{y:.1f}" '
            'stroke="var(--rh-border)" stroke-width="1"/>'
        )
        grid.append(
            f'<text x="{L - 12}" y="{y + 4:.1f}" text-anchor="end" '
            'fill="var(--rh-muted)" font-size="13" font-family="Inter,system-ui,sans-serif">'
            f'{q:.1f}</text>'
        )
        q += ystep
        guard += 1

    dots = []
    ordered = sorted(
        points,
        key=lambda p: (0 if p.source == B.ICARM_SOURCE else 1, p.rank_lower, p.source_id),
    )
    for idx, p in enumerate(ordered):
        value = p.metric(metric_key)
        if value is None:
            continue
        base_x = X(p.rank_lower)
        # Separate the two sources slightly when they occupy the same rank column.
        x = base_x + (-3.2 if p.source == B.LOCAL_SOURCE else 3.2)
        y = Y(value)
        radius = 5.8 if p.source == B.LOCAL_SOURCE else 5.1
        color = _source_color(p.source)
        opacity = _source_opacity(p.source)
        title = html.escape(
            f"{p.label} · {p.rank_evidence} · torsion {p.torsion_label or 'unknown'}"
            f" · {metric['label']} {_fmt_metric(value, metric_key)} · {p.detail}",
            quote=False,
        )
        circle = (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
            f'fill="{color}" fill-opacity="{opacity:.2f}" '
            f'stroke="{color}" stroke-opacity="{min(1.0, opacity + .18):.2f}" stroke-width="1.2">'
            f'<title>{title}</title></circle>'
        )
        if p.url:
            dots.append(
                f'<a href="{html.escape(p.url, quote=True)}" target="_blank" rel="noopener">{circle}</a>'
            )
        else:
            dots.append(circle)

    legend = (
        '<div class="lb-legend">'
        '<span><i style="background:var(--rh-primary)"></i>Rank Hunter</span>'
        '<span class="muted"><i style="background:var(--rh-muted)"></i>ICARM snapshot</span>'
        '</div>'
    )

    return f"""
    <div class="lb-chart-shell">
      {legend}
      <svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(metric['label'])} versus rank">
        {''.join(grid)}
        <line x1="{L}" y1="{T}" x2="{L}" y2="{T + plot_h}" stroke="var(--rh-muted-2)" stroke-width="1.5"/>
        <line x1="{L}" y1="{T + plot_h}" x2="{W - R}" y2="{T + plot_h}" stroke="var(--rh-muted-2)" stroke-width="1.5"/>
        <text x="{L + plot_w / 2:.1f}" y="{H - 12}" text-anchor="middle"
              fill="var(--rh-text-secondary)" font-size="15" font-family="Inter,system-ui,sans-serif">
          rank (rigorous lower bound) →
        </text>
        <text transform="rotate(-90)" x="{- (T + plot_h / 2):.1f}" y="24" text-anchor="middle"
              fill="var(--rh-text-secondary)" font-size="15" font-family="Inter,system-ui,sans-serif">
          {html.escape(metric["axis"])}
        </text>
        {''.join(dots)}
      </svg>
    </div>
    """


def _table_html(points, metric_key: str, limit: int = 250) -> str:
    rows = []
    for p in sorted(
        points,
        key=lambda x: (x.rank_lower, x.metric(metric_key) or math.inf, x.source, x.source_id),
    )[:limit]:
        value = p.metric(metric_key)
        name = html.escape(p.label)
        if p.url:
            name = (
                f'<a href="{html.escape(p.url, quote=True)}" target="_blank" rel="noopener">'
                f"{name}</a>"
            )
        rows.append(
            "<tr>"
            f"<td>{name}</td>"
            f"<td>{html.escape(p.rank_evidence)}</td>"
            f"<td>{html.escape(p.torsion_label or '—')}</td>"
            f"<td>{html.escape(p.detail)}</td>"
            f"<td class='num'>{_fmt_metric(value, metric_key)}</td>"
            f"<td class='mono'>{html.escape(p.conductor or '—')}</td>"
            "</tr>"
        )
    suffix = ""
    if len(points) > limit:
        suffix = f"<div class='lb-table-note'>Showing first {limit} of {len(points)} plotted rows.</div>"
    return (
        "<div class='lb-table-wrap'><table class='lb-table'>"
        "<thead><tr><th>curve</th><th>rank evidence</th><th>torsion</th><th>source detail</th>"
        f"<th>{html.escape(B.METRICS[metric_key]['label'])}</th><th>conductor</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>{suffix}"
    )


def _metric_card(point, metric_key: str) -> tuple[str, str]:
    if point is None:
        return ("—", "no recorded metric")
    value = point.metric(metric_key)
    return (
        _fmt_metric(value, metric_key),
        f"{point.label} · {point.rank_evidence} · torsion {point.torsion_label or 'unknown'}",
    )


def render(context):
    st.markdown(
        """
        <style>
        div[class*="st-key-leaderboard-compare-"] {
            color:var(--rh-text)!important;
            color-scheme:inherit;
        }
        div[class*="st-key-leaderboard-compare-"] label,
        div[class*="st-key-leaderboard-compare-"] p {
            color:var(--rh-text-secondary)!important;
        }
        div[class*="st-key-leaderboard-compare-"] [data-baseweb="select"] > div {
            background:var(--rh-card-2)!important;
            border-color:var(--rh-control-border,var(--rh-border-strong))!important;
            color:var(--rh-text)!important;
        }
        div[class*="st-key-leaderboard-compare-"] [data-baseweb="tag"] {
            background:var(--rh-surface-active)!important;
            color:var(--rh-text)!important;
        }
        div[class*="st-key-leaderboard-compare-"] input {
            color:var(--rh-text)!important;
            caret-color:var(--rh-primary)!important;
            accent-color:var(--rh-primary)!important;
        }
        div[class*="st-key-leaderboard-compare-"] [role="slider"] {
            background:var(--rh-primary)!important;
            border-color:var(--rh-primary)!important;
        }
        div[class*="st-key-leaderboard-compare-"] [data-testid="stRadio"],
        div[class*="st-key-leaderboard-compare-"] [data-testid="stSlider"],
        div[class*="st-key-leaderboard-compare-"] [data-testid="stSelectbox"],
        div[class*="st-key-leaderboard-compare-"] [data-testid="stMultiSelect"],
        div[class*="st-key-leaderboard-compare-"] [data-testid="stCheckbox"] {
            color:var(--rh-text-secondary)!important;
        }
        .lb-note {color:var(--rh-muted);font-size:.86rem;margin:.05rem 0 .65rem 0}
        .lb-chart-shell{position:relative;background:var(--rh-card);border:1px solid var(--rh-border);
            border-radius:16px;padding:14px 14px 4px 14px;box-shadow:0 12px 36px color-mix(in srgb,var(--rh-text) 10%,transparent);
            overflow:hidden}
        .lb-chart-shell svg{display:block;width:100%;height:auto}
        .lb-legend{display:flex;gap:18px;align-items:center;padding:1px 8px 7px 8px;
            color:var(--rh-text-secondary);font:600 12px Inter,system-ui,sans-serif}
        .lb-legend span{display:inline-flex;gap:7px;align-items:center}
        .lb-legend span.muted{color:var(--rh-muted)}
        .lb-legend i{width:9px;height:9px;border-radius:50%;display:inline-block}
        .lb-empty{background:var(--rh-card);border:1px solid var(--rh-border);border-radius:16px;
            color:var(--rh-muted);padding:34px 22px;text-align:center}
        .lb-table-wrap{overflow:auto;border:1px solid var(--rh-border);border-radius:12px;background:var(--rh-card)}
        .lb-table{width:100%;border-collapse:collapse;color:var(--rh-text-secondary);font-size:12px}
        .lb-table th{position:sticky;top:0;background:var(--rh-card-2);color:var(--rh-muted);text-align:left;
            padding:9px 10px;border-bottom:1px solid var(--rh-border);font-weight:700}
        .lb-table td{padding:8px 10px;border-bottom:1px solid var(--rh-border);vertical-align:top}
        .lb-table tr:last-child td{border-bottom:0}
        .lb-table a{color:var(--rh-primary);text-decoration:none}
        .lb-table a:hover{text-decoration:underline}
        .lb-table .num{text-align:right;font-variant-numeric:tabular-nums}
        .lb-table .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;max-width:360px;
            overflow-wrap:anywhere;color:var(--rh-muted)}
        .lb-table-note{color:var(--rh-muted);font-size:11px;margin-top:5px}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Leaderboard comparison: Rank Hunter's rigorous local lower bounds, with the locally "
        "synchronized ICARM catalog as a muted reference overlay."
    )

    available_lo, available_hi = B.rank_extent(context.db)
    slider_lo = max(1, available_lo)
    slider_hi = max(slider_lo, available_hi)
    default_lo = 17 if slider_hi >= 17 else slider_lo
    if default_lo < slider_lo:
        default_lo = slider_lo

    metric_key = st.radio(
        "Metric",
        options=list(B.METRICS),
        format_func=lambda key: B.METRICS[key]["label"],
        horizontal=True,
        label_visibility="collapsed",
        key="leaderboard-compare-metric",
    )

    controls = st.columns([1.25, 1.0, 1.15])
    with controls[0]:
        if slider_hi == slider_lo:
            rank_range = (slider_lo, slider_hi)
            st.caption(f"Rank lower bound: {slider_lo}")
        else:
            rank_range = st.slider(
                "Rank lower bound",
                min_value=slider_lo,
                max_value=slider_hi,
                value=(default_lo, slider_hi),
                step=1,
                key="leaderboard-compare-rank_range",
            )
    with controls[1]:
        view_mode = st.selectbox(
            "Plot",
            options=("Best per rank", "Record frontier", "All curves"),
            index=0,
            key="leaderboard-compare-view",
            help=(
                "Best per rank keeps the lowest metric separately for Rank Hunter and ICARM. "
                "Record frontier keeps only source records not beaten by an equal-or-higher rank."
            ),
        )
    with controls[2]:
        source_labels = st.multiselect(
            "Sources",
            options=("Rank Hunter", "ICARM"),
            default=("Rank Hunter", "ICARM"),
            key="leaderboard-compare-sources",
        )

    min_rank, max_rank = rank_range
    families = B.list_local_families(context.db, min_rank, max_rank)
    filter_cols = st.columns([1.35, 0.95, 1.0])
    with filter_cols[0]:
        selected_families = st.multiselect(
            "Rank Hunter families",
            options=families,
            default=[],
            key="leaderboard-compare-families",
            help="Leave empty to include every Rank Hunter family in the selected rank range.",
        )
    with filter_cols[1]:
        exact_only = st.checkbox(
            "Local exact-rank rows only",
            value=False,
            key="leaderboard-compare-exact_only",
            help="ICARM rows remain certified lower bounds; this filter applies only to Rank Hunter.",
        )

    points = []
    if "Rank Hunter" in source_labels:
        local = B.load_local_points(
            context.db,
            min_rank=min_rank,
            max_rank=max_rank,
            families=selected_families or None,
        )
        if exact_only:
            local = [p for p in local if p.rank_evidence.startswith("rank =")]
        points.extend(local)
    if "ICARM" in source_labels:
        points.extend(B.load_icarm_points(context.db, min_rank=min_rank, max_rank=max_rank))

    known_torsion, unknown_torsion = B.torsion_metadata_counts(points)
    torsion_options = ["Any", *B.torsion_groups(points)]
    with filter_cols[2]:
        torsion_choice = st.selectbox(
            "Torsion group",
            options=torsion_options,
            index=0,
            key="leaderboard-compare-torsion",
            help=(
                "Restrict both Rank Hunter and ICARM rows to one rational torsion group. "
                "Rank Hunter uses stored exact torsion; ICARM uses source-provided invariant factors."
            ),
        )

    if torsion_choice != "Any":
        points = B.filter_torsion(points, torsion_choice)
        if unknown_torsion:
            st.caption(
                f"Torsion filter: {torsion_choice} · {unknown_torsion:,} row(s) with unknown "
                "torsion metadata are excluded."
            )
    elif points and unknown_torsion:
        st.caption(
            f"Torsion metadata available for {known_torsion:,} of "
            f"{known_torsion + unknown_torsion:,} current row(s)."
        )

    metric_points = B.with_metric(points, metric_key)
    if view_mode == "Best per rank":
        plotted = B.best_per_rank(metric_points, metric_key)
    elif view_mode == "Record frontier":
        plotted = B.record_frontier(metric_points, metric_key)
    else:
        plotted = metric_points

    local_best = B.best_at_or_above(
        metric_points, metric_key, min_rank=min_rank, source=B.LOCAL_SOURCE
    )
    icarm_best = B.best_at_or_above(
        metric_points, metric_key, min_rank=min_rank, source=B.ICARM_SOURCE
    )
    local_value, local_caption = _metric_card(local_best, metric_key)
    icarm_value, icarm_caption = _metric_card(icarm_best, metric_key)

    cards = st.columns(3)
    cards[0].metric("Plotted curves", len(plotted))
    cards[1].metric(f"Best Rank Hunter ≥ {min_rank}", local_value)
    cards[1].caption(local_caption)
    cards[2].metric(f"Best ICARM ≥ {min_rank}", icarm_value)
    cards[2].caption(icarm_caption)

    if metric_key in ("naive", "faltings") and "Rank Hunter" in source_labels:
        st.markdown(
            "<div class='lb-note'>Rank Hunter's local <code>curves</code> rows do not currently "
            "persist ICARM-normalized naive/Faltings heights, so local dots are omitted on this tab.</div>",
            unsafe_allow_html=True,
        )

    st.markdown(_chart_html(plotted, metric_key, min_rank, max_rank), unsafe_allow_html=True)

    status = B.icarm_catalog_status(context.db)
    if "ICARM" in source_labels:
        if status is None:
            st.info(
                "No locally synchronized ICARM catalog metadata is present. "
                "The overlay stays offline and will remain empty until the catalog is synced."
            )
        else:
            fetched = status.get("fetched_at") or "unknown time"
            count = int(status.get("curve_count") or 0)
            st.caption(
                f"ICARM overlay: local snapshot with {count:,} curves, fetched {fetched}. "
                "External catalog rows are reference data only and do not alter Rank Hunter's local rank evidence."
            )

    with st.expander(f"Plotted rows ({len(plotted)})", expanded=False):
        if plotted:
            st.markdown(_table_html(plotted, metric_key), unsafe_allow_html=True)
        else:
            st.caption("No rows match the current plot filters.")
