"""Exact PGL2-chart search for the Mestre/Fermigier rank-11 sextuple family.

The native Mestre quartic is very effective at producing rational points, but
once a specialization has a substantial certified Mordell--Weil subgroup it
can become biased toward repeatedly exposing combinations of that subgroup.
This adapter changes *search coordinates*, not the curve:

    native C_t : y^2 = f_t(x)
        x = (A u + B)/(C u + D)
        v = (C u + D)^2 y
    chart C_t^M : v^2 = (C u + D)^4 f_t((A u + B)/(C u + D)).

Charts are selected by an operator-visible strategy. Base charts use triples
of the twelve exact Mestre base-fibre abscissas; subgroup-informed charts mix
those anchors with exact non-base native fibres discovered in prior searches;
free charts use small primitive PGL2(Q) matrices independent of known points;
and hybrid mode interleaves the three sources adaptively. Every ratpoints hit
is inverse mapped exactly to the native quartic and checked there before it is
mapped to E(Q).

The proof boundary is unchanged from ``mestre_quartic_search``: Neron--Tate
projection residuals only schedule work.  A rigorous lower bound changes only
after the exact quadratic-character independence certificate succeeds.
"""

from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction
from pathlib import Path

from sage.all import QQ

# Plugin workers are executed by absolute path.  When Rank Hunter is run from
# a source checkout, keep the core checkout importable without requiring the
# plugin itself to live inside that checkout.
import sys
_CORE_CWD = Path.cwd().resolve()
if (_CORE_CWD / "rank42").is_dir() and str(_CORE_CWD) not in sys.path:
    sys.path.insert(0, str(_CORE_CWD))

from rank42.timeouts import StageTimeout, hard_timeout
from rank42.db import connect, get_curve, get_curve_by_key, log_event, upsert_curve, update_curve
import family
from rank42.lattice_store import store_covering, update_covering
from native_search import (
    FAMILY_SPEC,
    RESULT_MARKER,
    _candidate_from_id,
    _candidate_rows,
    _canonical_parameter,
    _ensure_baseline_certificate,
    _fq,
    _load_stored_rigorous_basis,
    _point_key,
    _raw_row_parameter,
    _record_extra,
    _screen_candidates,
    _search_passes,
    _try_exact_growth,
)
from rank42.mobius_quartic import (
    build_chart_plan,
    evaluate,
    inverse_point,
    rational_height_bits,
    rank_exploratory_geometry_charts,
)
from rank42.quartic_store import create_or_get_search, finish_search, mark_running, store_points
from rank42.ratpoints import (
    RatpointsFailure,
    RatpointsNotFound,
    RatpointsTimeout,
    normalize_polynomial,
    probe_version,
    run_ratpoints,
)


def _parse_stages(text):
    values = []
    for piece in str(text).split(","):
        piece = piece.strip()
        if not piece:
            continue
        value = int(piece)
        if value <= 0:
            raise argparse.ArgumentTypeError("stage heights must be positive")
        values.append(value)
    values = sorted(set(values))
    if not values:
        raise argparse.ArgumentTypeError("at least one stage height is required")
    return values


def _parse_band_ceilings(text):
    """Parse ascending denominator-band ceilings; 'max' means the stage height."""
    out = []
    saw_max = False
    for piece in str(text or "").split(","):
        piece = piece.strip().lower()
        if not piece:
            continue
        if piece == "max":
            saw_max = True
            continue
        value = int(piece)
        if value < 1:
            raise argparse.ArgumentTypeError("denominator band ceilings must be positive")
        out.append(value)
    out = sorted(set(out))
    if not saw_max:
        saw_max = True
    return tuple(out), saw_max


def _denominator_bands(height, dl, du, args):
    """Return persistent denominator bands for one rational/nonintegral stage."""
    height = int(height)
    if not bool(args.banded_rational) or height < int(args.band_threshold):
        return [(dl, du)]

    start = max(1, int(dl) if dl is not None else 1)
    stop = min(height, int(du) if du is not None else height)
    if start > stop:
        return []
    ceilings, _saw_max = _parse_band_ceilings(args.denominator_bands)
    bands = []
    low = start
    for ceiling in ceilings:
        high = min(stop, int(ceiling))
        if high < low:
            continue
        bands.append((low, high))
        low = high + 1
        if low > stop:
            break
    if low <= stop:
        bands.append((low, stop))
    return bands


def _covering_payload(curve_id, bundle, chart, *, height, search_id, pass_name, chart_rank):
    A, B, C, D = chart.A, chart.B, chart.C, chart.D
    native_x = f"(({A})*u+({B}))/(({C})*u+({D}))"
    native_y = f"v/((({C})*u+({D}))^2)"
    return {
        "schema": "rank42.covering.v1",
        "curve_id": int(curve_id),
        "quartic": {
            "coefficients": [str(x) for x in chart.coefficients],
            "height": int(height),
        },
        "map": family.covering_map_expressions_from_native(
            bundle, native_x=native_x, native_y=native_y
        ),
        "metadata": {
            "source": "mestre_sextuple_pgl2_chart",
            "family_spec": FAMILY_SPEC,
            "declared_generic_rank": int(family.generic_rank),
            "quartic_search_id": int(search_id),
            "search_pass": str(pass_name),
            "chart_rank": int(chart_rank),
            "chart_strategy_source": str(chart.source),
            "chart": chart.as_metadata(),
            "proof_scope": "exact coordinate change; rank promotion requires exact independence certificate",
        },
    }


def _search_chart_stage(
    db,
    *,
    curve_id,
    param,
    score,
    chart,
    chart_rank,
    height,
    pass_name,
    dl,
    du,
    args,
    rpinfo,
):
    norm = normalize_polynomial(chart.coefficients)
    search = create_or_get_search(
        db,
        curve_id=curve_id,
        family=family.name(),
        parameter=param,
        hole_label=(
            f"mestre-pgl2-{chart_rank}-{pass_name}-"
            f"d{dl if dl is not None else 'min'}-{du if du is not None else 'max'}"
        ),
        coefficients=norm.rational_coefficients,
        integer_coefficients=norm.integer_coefficients,
        y_scale=norm.y_scale,
        degree=norm.degree,
        height_bound=height,
        denominator_low=dl,
        denominator_high=du,
        extra_args=args.extra_arg,
        metadata={
            "source": "mestre_sextuple_pgl2_chart",
            "family_spec": FAMILY_SPEC,
            "score": score,
            "chart_rank": int(chart_rank),
            "chart_strategy_source": str(chart.source),
            "chart": chart.as_metadata(),
            "search_pass": pass_name,
            "denominator_band": [
                int(dl) if dl is not None else None,
                int(du) if du is not None else None,
            ],
        },
    )

    if search["status"] == "done" and not args.force:
        print(
            f"    [mestre stage] mode=chart-{pass_name} H={height} "
            f"reuse search #{search['id']} points={search['point_count'] or 0}",
            flush=True,
        )
    else:
        mark_running(db, search["id"], executable=rpinfo["executable"])
        started = time.monotonic()
        try:
            stage_timeout = int(args.timeout)
            if pass_name in {"nonintegral", "rational"} and int(args.nonintegral_timeout or 0) > 0:
                stage_timeout = min(stage_timeout, int(args.nonintegral_timeout))
            result = run_ratpoints(
                norm.rational_coefficients,
                height,
                executable=rpinfo["executable"],
                timeout=stage_timeout,
                denominator_low=dl,
                denominator_high=du,
                extra_args=args.extra_arg,
            )
        except RatpointsTimeout as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="timeout", runtime=runtime, error=str(exc))
            print(
                f"    [mestre stage] mode=chart-{pass_name} H={height} "
                f"TIMEOUT after {stage_timeout}s",
                flush=True,
            )
            return search, [], "timeout"
        except RatpointsFailure as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="error", runtime=runtime, error=str(exc))
            print(
                f"    [mestre stage] mode=chart-{pass_name} H={height} ERROR {exc!r}",
                flush=True,
            )
            return search, [], "error"
        store_points(db, search["id"], result["points"])
        finish_search(
            db,
            search["id"],
            status="done",
            runtime=result["runtime"],
            point_count=len(result["points"]),
            error=None,
        )
        print(
            f"    [mestre stage] mode=chart-{pass_name} H={height} "
            f"points={len(result['points'])} runtime={result['runtime']:.3f}",
            flush=True,
        )

    rows = db.execute(
        "SELECT * FROM quartic_points WHERE search_id=? ORDER BY id",
        (search["id"],),
    ).fetchall()
    return search, rows, "done"


def _load_discovered_native_x(db, curve_id, base_x, *, limit=256):
    """Load exact non-base native x-fibres already mapped for this curve.

    Native-search rows store x directly. PGL2 rows persist the exact inverse
    image as ``metadata_json.native_x``. Requiring ``mapped_point_json`` keeps
    this anchor source downstream of the exact quartic->elliptic map rather
    than using raw ratpoints output. No subgroup-independence claim is made.
    """
    base = {_fq(x) for x in base_x}
    rows = db.execute(
        """
        SELECT qp.x AS chart_x, qp.metadata_json AS point_meta,
               qs.metadata_json AS search_meta
        FROM quartic_points qp
        JOIN quartic_searches qs ON qs.id=qp.search_id
        WHERE qs.curve_id=? AND qp.exact_verified=1
          AND qp.mapped_point_json IS NOT NULL
        ORDER BY qp.id ASC
        """,
        (int(curve_id),),
    ).fetchall()
    values = []
    seen = set()
    for rec in rows:
        try:
            pmeta = json.loads(rec["point_meta"] or "{}")
        except Exception:
            pmeta = {}
        try:
            smeta = json.loads(rec["search_meta"] or "{}")
        except Exception:
            smeta = {}
        source = str(smeta.get("source") or "")
        raw_x = pmeta.get("native_x")
        if raw_x is None and source == "mestre_sextuple_native_quartic":
            raw_x = rec["chart_x"]
        if raw_x is None:
            continue
        try:
            x = _fq(raw_x)
        except Exception:
            continue
        if x in base or x in seen:
            continue
        seen.add(x)
        values.append(x)

    values.sort(key=lambda x: (rational_height_bits(x), x))
    if int(limit) > 0 and len(values) > int(limit):
        # Deterministic spread through the full observed height range so the
        # anchor bank is not biased only toward the easiest rediscoveries.
        if int(limit) == 1:
            values = [values[len(values) // 2]]
        else:
            idxs = []
            for i in range(int(limit)):
                idx = round(i * (len(values) - 1) / (int(limit) - 1))
                if idx not in idxs:
                    idxs.append(idx)
            values = [values[i] for i in idxs]
    return values


def _mapped_native_records(db, curve_id):
    """Return exact mapped native fibres with discovery provenance."""
    rows = db.execute(
        """
        SELECT qp.id AS point_id, qp.x AS chart_x,
               qp.metadata_json AS point_meta,
               qs.metadata_json AS search_meta,
               qs.height_bound AS height_bound,
               qs.denominator_low AS denominator_low,
               qs.denominator_high AS denominator_high
        FROM quartic_points qp
        JOIN quartic_searches qs ON qs.id=qp.search_id
        WHERE qs.curve_id=? AND qp.exact_verified=1
          AND qp.mapped_point_json IS NOT NULL
        ORDER BY qp.id DESC
        """,
        (int(curve_id),),
    ).fetchall()
    out = []
    for rec in rows:
        try:
            pmeta = json.loads(rec["point_meta"] or "{}")
        except Exception:
            pmeta = {}
        try:
            smeta = json.loads(rec["search_meta"] or "{}")
        except Exception:
            smeta = {}
        source = str(smeta.get("source") or "")
        raw_x = pmeta.get("native_x")
        if raw_x is None and source == "mestre_sextuple_native_quartic":
            raw_x = rec["chart_x"]
        if raw_x is None:
            continue
        try:
            x = _fq(raw_x)
        except Exception:
            continue
        out.append(
            {
                "x": x,
                "point_id": int(rec["point_id"]),
                "height_bound": int(rec["height_bound"] or 0),
                "denominator_low": (
                    int(rec["denominator_low"])
                    if rec["denominator_low"] is not None
                    else None
                ),
                "denominator_high": (
                    int(rec["denominator_high"])
                    if rec["denominator_high"] is not None
                    else None
                ),
            }
        )
    return out


def _existing_native_x(db, curve_id):
    return {rec["x"] for rec in _mapped_native_records(db, curve_id)}


def _load_exploratory_native_x(
    db,
    curve_id,
    base_x,
    rigorous_x,
    *,
    limit=48,
    order="newest_high_denominator",
):
    """Load geometry-only fibres ordered by discovery/denominator novelty.

    These anchors remain search coordinates only. They are never inserted into
    the rigorous basis or used as rank evidence.
    """
    blocked = {_fq(x) for x in base_x}
    blocked.update(_fq(x) for x in rigorous_x)
    latest = {}
    for rec in _mapped_native_records(db, curve_id):
        x = rec["x"]
        if x in blocked or x in latest:
            continue
        latest[x] = rec
    records = list(latest.values())
    if not records:
        return [], {"available": 0, "selected": 0, "band_counts": {}}

    mode = str(order or "newest_high_denominator").strip().lower()
    if mode not in {"newest_high_denominator", "high_denominator", "newest", "high_height"}:
        raise ValueError(f"unknown exploratory anchor ordering: {mode}")

    for rec in records:
        x = rec["x"]
        rec["denominator_bits"] = int(x.denominator).bit_length()
        rec["height_bits"] = rational_height_bits(x)

    if mode == "newest":
        records.sort(key=lambda rec: (-rec["point_id"], -rec["denominator_bits"], rec["x"]))
    elif mode == "high_denominator":
        records.sort(
            key=lambda rec: (
                -rec["denominator_bits"],
                -int(rec["x"].denominator),
                -rec["point_id"],
                rec["x"],
            )
        )
    elif mode == "high_height":
        records.sort(
            key=lambda rec: (-rec["height_bits"], -rec["point_id"], rec["x"])
        )
    else:
        newest = sorted(records, key=lambda rec: (-rec["point_id"], rec["x"]))
        high_den = sorted(
            records,
            key=lambda rec: (
                -rec["denominator_bits"],
                -int(rec["x"].denominator),
                -rec["point_id"],
                rec["x"],
            ),
        )
        newest_rank = {rec["x"]: i for i, rec in enumerate(newest)}
        den_rank = {rec["x"]: i for i, rec in enumerate(high_den)}
        records.sort(
            key=lambda rec: (
                newest_rank[rec["x"]] + den_rank[rec["x"]],
                den_rank[rec["x"]],
                newest_rank[rec["x"]],
                rec["x"],
            )
        )

    selected = records[: max(0, int(limit))]
    band_counts = {}
    for rec in selected:
        low = rec["denominator_low"]
        high = rec["denominator_high"]
        label = f"{low if low is not None else 'min'}..{high if high is not None else 'max'}"
        band_counts[label] = int(band_counts.get(label, 0)) + 1
    return [rec["x"] for rec in selected], {
        "available": len(records),
        "selected": len(selected),
        "band_counts": band_counts,
    }


def _merge_count_maps(records, key):
    out = {}
    for rec in records:
        values = rec.get(key) or {}
        if not isinstance(values, dict):
            continue
        for name, value in values.items():
            out[str(name)] = int(out.get(str(name), 0)) + int(value or 0)
    return out


def parse_args():
    ap = argparse.ArgumentParser(
        description="Search exact PGL2 coordinate charts of the Mestre/Fermigier quartic."
    )
    ap.add_argument("--db", default="rank42.db")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--id", type=int, help="target one stored Mestre curve id")
    src.add_argument("--parameter", help="target one rational t and create/reuse its DB row")
    src.add_argument("--input", help="Nagao candidate JSONL; accepts t or a,b")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--mode", choices=["integer", "rational", "both"], default="both")
    ap.add_argument("--charts", type=int, default=12, help="top exact PGL2 charts per specialization")
    ap.add_argument(
        "--chart-strategy",
        choices=["base", "subgroup", "free", "hybrid", "fiber_expansion"],
        default="hybrid",
        help=(
            "PGL2 coordinate strategy; fiber_expansion mixes certified anchors "
            "with separately tagged geometry-only discovered fibres"
        ),
    )
    ap.add_argument(
        "--anchor-pool",
        type=int,
        default=12,
        help="lowest-height generic base-fibre x-values used by base/mixed charts",
    )
    ap.add_argument(
        "--discovered-anchor-pool",
        type=int,
        default=16,
        help="exact previously discovered non-base native fibres available to subgroup-informed charts",
    )
    ap.add_argument(
        "--free-bound",
        type=int,
        default=3,
        help="absolute entry bound for primitive integer free-PGL2 matrices",
    )
    ap.add_argument(
        "--exploratory-anchor-pool",
        type=int,
        default=48,
        help="geometry-only discovered native fibres available to fiber_expansion",
    )
    ap.add_argument(
        "--exploratory-order",
        choices=["newest_high_denominator", "high_denominator", "newest", "high_height"],
        default="newest_high_denominator",
        help="priority order for geometry-only exploratory fibres",
    )
    ap.add_argument(
        "--exploratory-mix",
        choices=["rigorous_heavy", "balanced", "exploratory_heavy"],
        default="balanced",
        help="mix of certified/exploratory anchors in second-generation charts",
    )
    ap.add_argument(
        "--stages",
        type=_parse_stages,
        default=_parse_stages("1000,10000"),
        help="comma-separated ratpoints heights in chart coordinates",
    )
    ap.add_argument("--timeout", type=int, default=20, help="ratpoints timeout per chart/pass/stage")
    ap.add_argument(
        "--nonintegral-timeout",
        type=int,
        default=0,
        help="optional stricter timeout for rational/nonintegral chart stages; 0 uses --timeout",
    )
    ap.add_argument(
        "--nonintegral-timeout-limit",
        type=int,
        default=0,
        help=(
            "adaptive circuit breaker: after this many timeouts in the same rational "
            "denominator band, skip that band on remaining charts; 0 disables the breaker"
        ),
    )
    ap.add_argument(
        "--banded-rational",
        action="store_true",
        help="split high rational/nonintegral stages into persistent denominator bands",
    )
    ap.add_argument(
        "--band-threshold",
        type=int,
        default=10000000,
        help="minimum height at which --banded-rational splits denominator space",
    )
    ap.add_argument(
        "--denominator-bands",
        default="10000,100000,1000000,3000000,max",
        help="comma-separated denominator ceilings for banded rational search; final max is clipped to stage height",
    )
    ap.add_argument(
        "--promotion-height",
        type=int,
        default=0,
        help="defer rational/nonintegral stages at or above this height until productive charts are ranked; 0 disables promotion",
    )
    ap.add_argument(
        "--promotion-charts",
        type=int,
        default=0,
        help="number of charts promoted to deferred high rational/nonintegral stages; 0 disables promotion",
    )
    ap.add_argument("--ratpoints")
    ap.add_argument("--extra-arg", action="append", default=[])
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--include-known-fibers",
        action="store_true",
        help="retain the twelve known native fibres as exact involution controls after inverse mapping",
    )
    ap.add_argument("--precision", type=int, default=256)
    ap.add_argument("--height-timeout", type=int, default=30)
    ap.add_argument("--subgroup-scan", type=int, default=512)
    ap.add_argument("--subgroup-chunk", type=int, default=24)
    ap.add_argument("--exact-candidates", type=int, default=12)
    ap.add_argument("--exact-control-candidates", type=int, default=1)
    ap.add_argument("--construction-timeout", type=int, default=120, help="hard timeout for exact native Mestre curve/quartic construction per candidate")
    ap.add_argument("--certificate-timeout", type=int, default=120)
    ap.add_argument("--novelty-rel-tol", type=float, default=1e-8)
    ap.add_argument(
        "--skip-baseline-certificate",
        action="store_true",
        help="discovery-only mode: do not certify the eleven displayed sections before searching",
    )
    return ap.parse_args()



def _scout_pgl2_quartics(db, *, curve_id, param, score, t, args, rpinfo):
    """Run exact PGL2 quartic scouts before materializing E(Q).

    Chart construction depends only on the native quartic, known native x-fibres
    and previously discovered native fibres.  The expensive elliptic model and
    its eleven specialized generic sections are needed only after a new native
    fibre survives exact inverse mapping.
    """
    setup_started = time.monotonic()
    native_coeffs = list(family.quartic_search_coefficients(t))
    native_poly = [_fq(c) for c in native_coeffs]
    known_native = family.native_quartic_known_points(t)
    known_x = {_fq(x) for x, _ in known_native}
    discovered_x = _load_discovered_native_x(
        db, curve_id, known_x, limit=max(int(args.discovered_anchor_pool), 1) * 8
    )
    existing_native_before = _existing_native_x(db, curve_id)
    exploratory_x = []
    exploratory_meta = {"available": 0, "selected": 0, "band_counts": {}}
    print(
        f"    cheap PGL2 scout setup ready in {time.monotonic()-setup_started:.3f}s; "
        "elliptic model deferred until a hit",
        flush=True,
    )

    if str(args.chart_strategy) == "fiber_expansion":
        exploratory_x, exploratory_meta = _load_exploratory_native_x(
            db,
            curve_id,
            known_x,
            discovered_x,
            limit=int(args.exploratory_anchor_pool),
            order=str(args.exploratory_order),
        )
        print(
            f"    ranking second-generation charts certified_anchors="
            f"{len(set(known_x) | set(discovered_x))} "
            f"geometry_only={len(exploratory_x)}/{int(exploratory_meta.get('available') or 0)} "
            f"order={args.exploratory_order} mix={args.exploratory_mix}",
            flush=True,
        )
        if exploratory_meta.get("band_counts"):
            band_text = ", ".join(
                f"{band}:{count}"
                for band, count in sorted(exploratory_meta["band_counts"].items())
            )
            print(
                f"    [mestre exploratory] selected anchor source bands {band_text}",
                flush=True,
            )
        charts = rank_exploratory_geometry_charts(
            native_coeffs,
            known_x,
            discovered_x,
            exploratory_x,
            rigorous_anchor_pool=max(3, int(args.anchor_pool)),
            exploratory_anchor_pool=int(args.exploratory_anchor_pool),
            mix=str(args.exploratory_mix),
            limit=int(args.charts),
        )
        if not charts:
            print(
                "    [mestre exploratory] no geometry-only anchors available; "
                "falling back to hybrid chart planning",
                flush=True,
            )
            charts = build_chart_plan(
                native_coeffs,
                known_x,
                discovered_x,
                strategy="hybrid",
                anchor_pool=int(args.anchor_pool),
                discovered_anchor_pool=int(args.discovered_anchor_pool),
                free_bound=int(args.free_bound),
                limit=int(args.charts),
            )
    else:
        print(
            f"    ranking exact PGL2 charts strategy={args.chart_strategy} "
            f"base_anchors={min(int(args.anchor_pool), len(known_x))} "
            f"discovered_fibres={len(discovered_x)} free_bound={int(args.free_bound)}...",
            flush=True,
        )
        charts = build_chart_plan(
            native_coeffs,
            known_x,
            discovered_x,
            strategy=args.chart_strategy,
            anchor_pool=int(args.anchor_pool),
            discovered_anchor_pool=int(args.discovered_anchor_pool),
            free_bound=int(args.free_bound),
            limit=int(args.charts),
        )
    if not charts:
        return {
            "native_coeffs": native_coeffs,
            "native_poly": native_poly,
            "known_native": known_native,
            "known_x": known_x,
            "discovered_x": discovered_x,
            "charts": [],
            "native_hits": {},
            "new_x": set(),
            "timeouts": 0,
            "stage_errors": 0,
            "stage_count": 0,
            "charts_searched": 0,
            "promoted_charts": 0,
            "banded_rational": bool(args.banded_rational),
            "exploratory_anchor_fibres": len(exploratory_x),
            "exploratory_anchor_available": int(exploratory_meta.get("available") or 0),
            "exploratory_band_counts": dict(exploratory_meta.get("band_counts") or {}),
            "new_fiber_band_counts": {},
        }
    for j, chart in enumerate(charts, 1):
        print(
            f"    chart {j}: source={chart.source} quality={chart.quality:.1f} "
            f"coeffbits={chart.max_coeff_bits} knownbits={chart.max_known_bits} "
            f"anchors=({chart.alpha},{chart.beta},{chart.gamma})",
            flush=True,
        )

    native_hits = {}
    timeouts = 0
    stage_errors = 0
    stage_count = 0
    charts_searched = 0
    band_timeout_counts = {}
    band_circuit_announced = set()
    chart_productivity = {j: set() for j in range(1, len(charts) + 1)}
    new_fiber_owner = {}
    new_fiber_band_counts = {}
    deferred = []

    def _rational_pass(pass_name):
        return pass_name in {"nonintegral", "rational"}

    def _band_key(height, dl, du):
        return (
            int(height),
            int(dl) if dl is not None else None,
            int(du) if du is not None else None,
        )

    def _band_label(dl, du):
        return f"d={dl if dl is not None else 'min'}..{du if du is not None else 'max'}"

    def _consume_rows(j, chart, search, height, pass_name, qrows):
        for qrow in qrows:
            mapped_native = inverse_point(chart, qrow["x"], qrow["y"])
            if mapped_native is None:
                continue
            x, y = mapped_native
            if y * y != evaluate(native_poly, x):
                raise ArithmeticError("Mestre PGL2 inverse failed exact native-quartic check")
            meta = json.loads(qrow["metadata_json"] or "{}")
            meta.update(
                {
                    "native_x": str(x),
                    "native_y": str(y),
                    "pgl2_chart": chart.as_metadata(),
                    "inverse_map_verified_exactly": True,
                    "discovery_height": int(height),
                    "discovery_denominator_band": [
                        int(search["denominator_low"])
                        if search["denominator_low"] is not None
                        else None,
                        int(search["denominator_high"])
                        if search["denominator_high"] is not None
                        else None,
                    ],
                }
            )
            db.execute(
                "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                (json.dumps(meta, sort_keys=True), qrow["id"]),
            )
            db.commit()
            if (
                x not in known_x
                and x not in existing_native_before
                and x not in new_fiber_owner
            ):
                new_fiber_owner[x] = int(j)
                chart_productivity[int(j)].add(x)
                band_label = (
                    f"{search['denominator_low'] if search['denominator_low'] is not None else 'min'}.."
                    f"{search['denominator_high'] if search['denominator_high'] is not None else 'max'}"
                )
                new_fiber_band_counts[band_label] = (
                    int(new_fiber_band_counts.get(band_label, 0)) + 1
                )
            if not args.include_known_fibers and x in known_x:
                continue
            native_hits.setdefault(
                (x, y),
                {
                    "qrow": qrow,
                    "search": search,
                    "height": int(height),
                    "pass_name": pass_name,
                    "chart": chart,
                    "chart_rank": int(j),
                    "x": x,
                    "y": y,
                },
            )

    def _run_one_band(j, chart, *, height, pass_name, dl, du):
        nonlocal timeouts, stage_errors, stage_count
        key = _band_key(height, dl, du)
        limit = int(args.nonintegral_timeout_limit or 0)
        if _rational_pass(pass_name) and limit > 0 and int(band_timeout_counts.get(key, 0)) >= limit:
            marker = (key, limit)
            if marker not in band_circuit_announced:
                print(
                    f"    [mestre adaptive] H={int(height)} {_band_label(dl, du)} "
                    f"disabled after {limit} timeout(s); continuing other bands/charts",
                    flush=True,
                )
                band_circuit_announced.add(marker)
            return "blocked"

        stage_count += 1
        search, qrows, status = _search_chart_stage(
            db,
            curve_id=curve_id,
            param=param,
            score=score,
            chart=chart,
            chart_rank=j,
            height=height,
            pass_name=pass_name,
            dl=dl,
            du=du,
            args=args,
            rpinfo=rpinfo,
        )
        if status == "timeout":
            timeouts += 1
            if _rational_pass(pass_name):
                band_timeout_counts[key] = int(band_timeout_counts.get(key, 0)) + 1
            return status
        if status == "error":
            stage_errors += 1
            return status
        _consume_rows(j, chart, search, height, pass_name, qrows)
        return status

    def _run_height(j, chart, *, height, pass_name, dl, du):
        bands = (
            _denominator_bands(height, dl, du, args)
            if _rational_pass(pass_name)
            else [(dl, du)]
        )
        if len(bands) > 1:
            print(
                f"    [mestre bands] chart {j} H={int(height)} "
                f"{len(bands)} denominator bands",
                flush=True,
            )
        for band_dl, band_du in bands:
            status = _run_one_band(
                j,
                chart,
                height=height,
                pass_name=pass_name,
                dl=band_dl,
                du=band_du,
            )
            if status in {"timeout", "error"}:
                # Bound heat and preserve resumability: lose at most one band on
                # this chart, then move on. Completed bands stay cached.
                break

    promotion_enabled = (
        int(args.promotion_height or 0) > 0
        and int(args.promotion_charts or 0) > 0
    )
    for j, chart in enumerate(charts, 1):
        print(f"    [chart {j}/{len(charts)}]", flush=True)
        charts_searched += 1
        for pass_name, dl, du in _search_passes(args.mode):
            stop_pass = False
            for height in args.stages:
                if stop_pass:
                    break
                if (
                    promotion_enabled
                    and _rational_pass(pass_name)
                    and int(height) >= int(args.promotion_height)
                ):
                    deferred.append((j, chart, pass_name, dl, du, int(height)))
                    continue
                before_timeouts = timeouts
                before_errors = stage_errors
                _run_height(
                    j,
                    chart,
                    height=height,
                    pass_name=pass_name,
                    dl=dl,
                    du=du,
                )
                # Preserve the old cheap-stage behavior: a failed monolithic
                # pass does not keep escalating that same chart.
                if (
                    not (
                        _rational_pass(pass_name)
                        and bool(args.banded_rational)
                        and int(height) >= int(args.band_threshold)
                    )
                    and (timeouts > before_timeouts or stage_errors > before_errors)
                ):
                    stop_pass = True

    promoted = []
    if deferred:
        wanted = min(max(1, int(args.promotion_charts)), len(charts))
        ranked_chart_ids = sorted(
            range(1, len(charts) + 1),
            key=lambda j: (-len(chart_productivity[j]), j),
        )
        promoted = ranked_chart_ids[:wanted]
        productive = sum(bool(chart_productivity[j]) for j in promoted)
        new_yield = sum(len(chart_productivity[j]) for j in promoted)
        print(
            f"    [mestre promotion] deferred high rational work -> "
            f"top {len(promoted)}/{len(charts)} charts by new-fibre yield "
            f"({productive} productive charts, {new_yield} new fibre(s))",
            flush=True,
        )
        print(
            "    [mestre promotion] charts="
            + ",".join(
                f"{j}:{len(chart_productivity[j])}"
                for j in promoted
            ),
            flush=True,
        )
        promoted_set = set(promoted)
        for j, chart, pass_name, dl, du, height in deferred:
            if j not in promoted_set:
                continue
            print(
                f"    [promoted chart {j}/{len(charts)}] "
                f"mode={pass_name} H={height}",
                flush=True,
            )
            _run_height(
                j,
                chart,
                height=height,
                pass_name=pass_name,
                dl=dl,
                du=du,
            )

    new_x = set(new_fiber_owner)
    return {
        "native_coeffs": native_coeffs,
        "native_poly": native_poly,
        "known_native": known_native,
        "known_x": known_x,
        "discovered_x": discovered_x,
        "charts": charts,
        "native_hits": native_hits,
        "new_x": new_x,
        "timeouts": timeouts,
        "stage_errors": stage_errors,
        "stage_count": stage_count,
        "charts_searched": charts_searched,
        "promoted_charts": len(promoted),
        "banded_rational": bool(args.banded_rational),
        "band_timeout_counts": {
            f"{height}:{dl}:{du}": int(count)
            for (height, dl, du), count in band_timeout_counts.items()
        },
        "exploratory_anchor_fibres": len(exploratory_x),
        "exploratory_anchor_available": int(exploratory_meta.get("available") or 0),
        "exploratory_band_counts": dict(exploratory_meta.get("band_counts") or {}),
        "new_fiber_band_counts": dict(new_fiber_band_counts),
    }


def _negative_pgl2_scout_result(db, *, curve_id, param, started, args, scout):
    row = get_curve(db, curve_id)
    rigorous = max(int(row["descent_lower"] or 0), int(row["exact_rank"] or 0))
    if row["exact_rank"] is None:
        update_curve(db, curve_id, status="extra_done", error=None)
    charts = list(scout["charts"])
    print("    no new native quartic x-fibres -> no elliptic model needed", flush=True)
    return {
        "curve_id": curve_id,
        "parameter": param,
        "status": "extra_done",
        "current_lower_before": rigorous,
        "best_rigorous_lower": rigorous,
        "baseline_certificate_status": "deferred_no_hit",
        "search_geometry": "pgl2",
        "search_mode": f"pgl2-{args.mode}",
        "chart_strategy": str(args.chart_strategy),
        "discovered_anchor_fibres": len(scout["discovered_x"]),
        "charts_base": sum(chart.source == "base" for chart in charts),
        "charts_subgroup": sum(chart.source == "subgroup" for chart in charts),
        "charts_free": sum(chart.source == "free" for chart in charts),
        "charts_exploratory": sum(chart.source == "exploratory" for chart in charts),
        "exploratory_anchor_fibres": int(scout.get("exploratory_anchor_fibres") or 0),
        "exploratory_anchor_available": int(scout.get("exploratory_anchor_available") or 0),
        "exploratory_band_counts": dict(scout.get("exploratory_band_counts") or {}),
        "new_fiber_band_counts": dict(scout.get("new_fiber_band_counts") or {}),
        "charts_searched": int(scout["charts_searched"]),
        "promoted_charts": int(scout.get("promoted_charts") or 0),
        "banded_rational": bool(scout.get("banded_rational")),
        "quartic_stages_checked": int(scout["stage_count"]),
        "ratpoints_timeouts": int(scout["timeouts"]),
        "stage_errors": int(scout["stage_errors"]),
        "new_native_fibers": 0,
        "mapped_extra_points": 0,
        "involution_controls_classified": 0,
        "subgroup_candidates_screened": 0,
        "height_chunk_failures": 0,
        "numerically_novel_candidates": 0,
        "best_novelty_relative_residual": None,
        "exact_candidate_attempts": 0,
        "exact_dependent": 0,
        "exact_inconclusive": 0,
        "exact_errors": 0,
        "exact_scheduled_novel": 0,
        "exact_scheduled_controls": 0,
        "exact_skipped_non_novel": 0,
        "exact_rank_growth": 0,
        "best_screened_rank": rigorous,
        "runtime_seconds": time.monotonic() - started,
    }


def _run_one(db, cand, args, rpinfo, index, total):
    started = time.monotonic()
    t = QQ(str(cand["t"]))
    if t == 0:
        raise ValueError("Mestre sextuple construction degenerates at t=0")
    param = str(t)
    score = float(cand.get("score", 0.0))
    curve_id = cand.get("curve_id")
    if curve_id is None:
        existing = get_curve_by_key(db, family.name(), param)
        curve_id = int(existing["id"]) if existing is not None else upsert_curve(
            db, family=family.name(), parameter=param, score=score
        )
    curve_id = int(curve_id)

    print()
    print(f"[{index}/{total}] curve #{curve_id} t={param} score={score:.6f}", flush=True)
    print("    scouting exact Mestre PGL2 quartics first...", flush=True)
    try:
        scout = _scout_pgl2_quartics(
            db, curve_id=curve_id, param=param, score=score, t=t, args=args, rpinfo=rpinfo
        )
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Mestre PGL2 scout failed: {exc!r}")
        print("    SCOUT ERROR:", repr(exc), flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "scout_error",
            "error": repr(exc),
            "runtime_seconds": time.monotonic() - started,
        }

    if not scout["charts"]:
        if args.chart_strategy == "subgroup" and not scout["discovered_x"]:
            print("    no subgroup-informed charts: no exact non-base fibres have been mapped yet", flush=True)
        else:
            print("    no usable PGL2 charts", flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "no_charts",
            "runtime_seconds": time.monotonic() - started,
        }

    new_x = set(scout["new_x"])
    if not new_x and not args.include_known_fibers:
        return _negative_pgl2_scout_result(
            db, curve_id=curve_id, param=param, started=started, args=args, scout=scout
        )

    if new_x:
        print(f"    NEW NATIVE QUARTIC HIT(S): {len(new_x)} new x-fibre(s)", flush=True)
    print("    hit found; materializing exact Mestre elliptic model + 11 sections...", flush=True)
    construction_started = time.monotonic()
    try:
        with hard_timeout(args.construction_timeout, "Mestre exact native construction"):
            bundle = family.direct_search_bundle(t)
    except StageTimeout as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "timeout", f"Mestre exact construction timeout: {exc}")
        print("    CONSTRUCTION TIMEOUT:", str(exc), flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "construction_timeout",
            "error": str(exc),
            "runtime_seconds": time.monotonic() - started,
        }
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Mestre PGL2 model construction failed: {exc!r}")
        print("    CONSTRUCTION ERROR:", repr(exc), flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "construction_error",
            "error": repr(exc),
            "runtime_seconds": time.monotonic() - started,
        }
    print(f"    exact elliptic materialization complete in {time.monotonic()-construction_started:.3f}s", flush=True)

    E = bundle["curve"]
    family_basis = list(bundle["basis"])
    native_coeffs = list(scout["native_coeffs"])
    native_poly = list(scout["native_poly"])
    known_native = list(scout["known_native"])
    known_x = set(scout["known_x"])

    row = get_curve(db, curve_id)
    try:
        stored_ainvs = json.loads(row["a_invariants_json"] or "null")
    except Exception:
        stored_ainvs = None
    current_ainvs = [str(a) for a in E.a_invariants()]
    if stored_ainvs and [str(x) for x in stored_ainvs] != current_ainvs and int(row["descent_lower"] or 0) > 0:
        msg = (
            "stored Mestre curve model differs from the current deterministic family model while rigorous generators exist; "
            "refusing to overwrite witness coordinates"
        )
        update_curve(db, curve_id, status="error", error=msg)
        log_event(db, curve_id, "error", msg)
        print("    MODEL MISMATCH:", msg, flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "model_mismatch",
            "error": msg,
            "runtime_seconds": time.monotonic() - started,
        }

    update_curve(
        db,
        curve_id,
        a_invariants_json=json.dumps(current_ainvs),
        status="exact" if row["exact_rank"] is not None else "extra_searching",
        error=None,
    )
    row = get_curve(db, curve_id)
    current_lower_before = max(int(row["descent_lower"] or 0), int(row["exact_rank"] or 0))

    rigorous_basis = _load_stored_rigorous_basis(E, row)
    baseline_cert = None
    if not rigorous_basis and not args.skip_baseline_certificate:
        rigorous_basis, baseline_cert = _ensure_baseline_certificate(
            db, row, E, family_basis, args.certificate_timeout
        )
        row = get_curve(db, curve_id)
    elif rigorous_basis:
        baseline_cert = {"status": "stored_rigorous_basis", "independent": True}

    screen_basis = list(rigorous_basis) if rigorous_basis else list(family_basis)
    exact_seed_basis = list(rigorous_basis) if rigorous_basis else list(family_basis)

    involution_control_keys = {}
    if args.include_known_fibers:
        controls = family.native_quartic_involution_controls(bundle, t)
        for control in controls:
            P = control["opposite_image"]
            if not P.is_zero():
                involution_control_keys[_point_key(P)] = int(control["index"])
        print(
            f"    positive control: exact quartic involution verified on {len(controls)} base fibres",
            flush=True,
        )

    # The cheap scout already ranked charts, ran ratpoints and inverse-mapped
    # every hit exactly to the native quartic.  Do not pay that work twice.
    discovered_x = list(scout["discovered_x"])
    charts = list(scout["charts"])
    native_hits = dict(scout["native_hits"])
    timeouts = int(scout["timeouts"])
    stage_errors = int(scout["stage_errors"])
    stage_count = int(scout["stage_count"])
    charts_searched = int(scout["charts_searched"])
    new_x = set(scout["new_x"])

    known_E = {_point_key(P) for P in family_basis if not P.is_zero()}
    known_E.update(_point_key(P) for P in rigorous_basis if not P.is_zero())
    mapped = []
    seen_E = set()
    controls_classified = 0
    for hit in native_hits.values():
        qrow = hit["qrow"]
        try:
            P = family.map_native_quartic_point(bundle, hit["x"], hit["y"])
        except Exception as exc:
            meta = json.loads(qrow["metadata_json"] or "{}")
            meta["elliptic_map_error"] = repr(exc)
            db.execute(
                "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                (json.dumps(meta, sort_keys=True), qrow["id"]),
            )
            db.commit()
            continue
        if P.is_zero():
            continue
        key = _point_key(P)
        if key in seen_E:
            continue
        seen_E.add(key)
        db.execute(
            "UPDATE quartic_points SET mapped_point_json=? WHERE id=?",
            (json.dumps([str(P[0]), str(P[1])]), qrow["id"]),
        )
        db.commit()
        if key in known_E:
            continue
        if key in involution_control_keys:
            controls_classified += 1
            meta = json.loads(qrow["metadata_json"] or "{}")
            meta.update(
                {
                    "classification": "known_quartic_involution_control",
                    "base_fibre_index": involution_control_keys[key],
                    "proof_status": "exact_structural_identity",
                }
            )
            db.execute(
                "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                (json.dumps(meta, sort_keys=True), qrow["id"]),
            )
            db.commit()
            continue

        covering = store_covering(
            db,
            _covering_payload(
                curve_id,
                bundle,
                hit["chart"],
                height=hit["height"],
                search_id=hit["search"]["id"],
                pass_name=hit["pass_name"],
                chart_rank=hit["chart_rank"],
            ),
        )
        update_covering(
            db,
            covering["id"],
            quartic_search_id=hit["search"]["id"],
            status="mapped",
        )
        mapped.append(
            {
                "curve_id": curve_id,
                "qrow_id": int(qrow["id"]),
                "covering_id": int(covering["id"]),
                "point": P,
                "native_x": str(hit["x"]),
                "native_y": str(hit["y"]),
                "height": hit["height"],
                "pass_name": hit["pass_name"],
                "chart_rank": hit["chart_rank"],
                "chart_strategy_source": str(hit["chart"].source),
                "precision_bits": int(args.precision),
                "source": "mestre_pgl2_ratpoints",
            }
        )

    print(f"    mapped unique points outside listed basis = {len(mapped)}", flush=True)

    ranked = []
    height_failures = []
    if mapped:
        ranked, height_failures = _screen_candidates(E, screen_basis, mapped, args)
        if ranked:
            numerical_new = sum(
                float(rec.get("relative_residual", 0.0)) > float(args.novelty_rel_tol)
                for rec in ranked
            )
            best_rel = float(ranked[0]["relative_residual"])
            print(
                f"    [mestre novelty] screened={len(ranked)} numerical_new={numerical_new} "
                f"best_rel_residual={best_rel:.6g}",
                flush=True,
            )
        else:
            print("    [mestre novelty] numerical subgroup screen unavailable", flush=True)

    ranked_keys = {_point_key(rec["point"]): rec for rec in ranked}
    for rec in mapped:
        key = _point_key(rec["point"])
        source_rec = ranked_keys.get(key, rec)
        source_rec.setdefault("source", "mestre_pgl2_ratpoints")
        rel = source_rec.get("relative_residual")
        numerical_new = bool(rel is not None and float(rel) > float(args.novelty_rel_tol))
        _record_extra(
            db,
            source_rec,
            before=len(screen_basis),
            numerical_new=numerical_new,
            screen_after=(len(screen_basis) + 1 if numerical_new else len(screen_basis)),
            exact_status="not_attempted",
        )

    unranked = [rec for rec in mapped if _point_key(rec["point"]) not in ranked_keys]
    exact_order = list(ranked) + unranked
    if mapped:
        exact_basis, exact_counts = _try_exact_growth(
            db, row, E, exact_seed_basis, exact_order, args
        )
    else:
        exact_basis = exact_seed_basis
        exact_counts = {
            "attempts": 0,
            "dependent": 0,
            "inconclusive": 0,
            "errors": 0,
            "growth": 0,
            "scheduled_novel": 0,
            "scheduled_controls": 0,
            "skipped_non_novel": 0,
        }

    final_row = get_curve(db, curve_id)
    rigorous_after = max(int(final_row["descent_lower"] or 0), int(final_row["exact_rank"] or 0))
    best_screened = len(screen_basis)
    if ranked and any(
        float(rec.get("relative_residual", 0.0)) > float(args.novelty_rel_tol)
        for rec in ranked
    ):
        best_screened += 1
    best_screened = max(best_screened, rigorous_after)

    if exact_counts["growth"]:
        final_status = "proven_lower"
    elif mapped:
        final_status = "extra_review"
    else:
        final_status = "extra_done"
    if final_row["exact_rank"] is None:
        update_curve(db, curve_id, status=final_status, error=None)

    return {
        "curve_id": curve_id,
        "parameter": param,
        "status": final_status,
        "current_lower_before": current_lower_before,
        "best_rigorous_lower": rigorous_after,
        "baseline_certificate_status": (baseline_cert or {}).get("status") if baseline_cert else "skipped",
        "search_geometry": "pgl2",
        "search_mode": f"pgl2-{args.mode}",
        "chart_strategy": str(args.chart_strategy),
        "discovered_anchor_fibres": len(discovered_x),
        "charts_base": sum(chart.source == "base" for chart in charts),
        "charts_subgroup": sum(chart.source == "subgroup" for chart in charts),
        "charts_free": sum(chart.source == "free" for chart in charts),
        "charts_exploratory": sum(chart.source == "exploratory" for chart in charts),
        "exploratory_anchor_fibres": int(scout.get("exploratory_anchor_fibres") or 0),
        "exploratory_anchor_available": int(scout.get("exploratory_anchor_available") or 0),
        "exploratory_band_counts": dict(scout.get("exploratory_band_counts") or {}),
        "new_fiber_band_counts": dict(scout.get("new_fiber_band_counts") or {}),
        "charts_searched": charts_searched,
        "promoted_charts": int(scout.get("promoted_charts") or 0),
        "banded_rational": bool(scout.get("banded_rational")),
        "quartic_stages_checked": stage_count,
        "ratpoints_timeouts": timeouts,
        "stage_errors": stage_errors,
        "new_native_fibers": len(new_x),
        "mapped_extra_points": len(mapped),
        "involution_controls_classified": controls_classified,
        "subgroup_candidates_screened": len(ranked),
        "height_chunk_failures": len(height_failures),
        "numerically_novel_candidates": sum(
            float(rec.get("relative_residual", 0.0)) > float(args.novelty_rel_tol)
            for rec in ranked
        ),
        "best_novelty_relative_residual": (
            float(ranked[0]["relative_residual"]) if ranked else None
        ),
        "exact_candidate_attempts": exact_counts["attempts"],
        "exact_dependent": exact_counts["dependent"],
        "exact_inconclusive": exact_counts["inconclusive"],
        "exact_errors": exact_counts["errors"],
        "exact_scheduled_novel": exact_counts.get("scheduled_novel", 0),
        "exact_scheduled_controls": exact_counts.get("scheduled_controls", 0),
        "exact_skipped_non_novel": exact_counts.get("skipped_non_novel", 0),
        "exact_rank_growth": exact_counts["growth"],
        "best_screened_rank": best_screened,
        "runtime_seconds": time.monotonic() - started,
    }


def main():
    args = parse_args()
    db = connect(args.db)
    try:
        try:
            rpinfo = probe_version(args.ratpoints)
        except RatpointsNotFound as exc:
            raise SystemExit(str(exc))

        if args.id is not None:
            candidates = [_candidate_from_id(db, args.id)]
        elif args.parameter is not None:
            raw_t = QQ(str(args.parameter))
            candidates = [{"t": str(_canonical_parameter(raw_t)), "raw_t": str(raw_t), "score": 0.0}]
        else:
            candidates = []
            seen_orbits = {}
            for raw_index, raw in enumerate(_candidate_rows(args.input, args.limit), 1):
                declared = raw.get("family")
                spec = raw.get("family_spec")
                if declared and declared != family.name():
                    raise SystemExit(
                        f"candidate family {declared!r} does not match {family.name()!r}"
                    )
                if spec and spec not in {FAMILY_SPEC, "mestre-rank11"}:
                    raise SystemExit(
                        f"candidate family_spec {spec!r} is not the Mestre sextuple adapter"
                    )
                raw_t = _raw_row_parameter(raw)
                canonical_t = str(_canonical_parameter(raw_t))
                orbit_key = family.parameter_orbit_key(raw_t)
                duplicate_of = seen_orbits.get(orbit_key)
                if duplicate_of is None:
                    seen_orbits[orbit_key] = raw_index
                candidates.append(
                    {
                        "t": canonical_t,
                        "raw_t": str(raw_t),
                        "score": float(raw.get("score", 0.0)),
                        "symmetry_duplicate_of": duplicate_of,
                    }
                )

        print("RANK HUNTER MESTRE PGL2-CHART SEARCH")
        print("=" * 72)
        print("family              =", family.name())
        print("parameter symmetry  = t ~ -t (candidate pools canonicalized)")
        print("search geometry     = exact PGL2(Q) charts of the native quartic")
        print("ratpoints           =", rpinfo["executable"])
        print("ratpoints version   =", rpinfo["version"] or "unknown")
        print("candidates          =", len(candidates))
        print("chart search mode   =", args.mode)
        print("chart strategy      =", args.chart_strategy)
        print("charts/candidate    =", args.charts)
        print("base anchor pool    =", args.anchor_pool)
        print("discovered pool     =", args.discovered_anchor_pool)
        print("free matrix bound   =", args.free_bound)
        if args.chart_strategy == "fiber_expansion":
            print("exploratory pool    =", args.exploratory_anchor_pool)
            print("exploratory order   =", args.exploratory_order)
            print("exploratory mix     =", args.exploratory_mix)
            print("exploratory proof   = geometry only; never rank evidence")
        print("height stages       =", ",".join(str(x) for x in args.stages))
        print("timeout/chart-stage =", args.timeout, "s")
        print(
            "nonintegral cap     =",
            (str(args.nonintegral_timeout) + " s" if int(args.nonintegral_timeout or 0) > 0 else "same as stage timeout"),
        )
        print(
            "nonintegral circuit =",
            (f"{int(args.nonintegral_timeout_limit)} timeout(s)/band" if int(args.nonintegral_timeout_limit or 0) > 0 else "disabled"),
        )
        print(
            "banded rational     =",
            (
                f"on at H>={int(args.band_threshold)} · {args.denominator_bands}"
                if args.banded_rational
                else "off"
            ),
        )
        print(
            "chart promotion     =",
            (
                f"top {int(args.promotion_charts)} at H>={int(args.promotion_height)}"
                if int(args.promotion_height or 0) > 0 and int(args.promotion_charts or 0) > 0
                else "off"
            ),
        )
        print("height precision    =", args.precision, "bits (numerical screen only)")
        print("height timeout      =", args.height_timeout, "s/chunk")
        print("construction timeout=", args.construction_timeout, "s/candidate")
        print("certificate timeout =", args.certificate_timeout, "s/attempt")
        print("known base fibres   =", "included" if args.include_known_fibers else "skipped")

        results = []
        for index, cand in enumerate(candidates, 1):
            duplicate_of = cand.get("symmetry_duplicate_of")
            if duplicate_of is not None:
                print()
                print(
                    f"[{index}/{len(candidates)}] t={cand.get('raw_t')} -> canonical t={cand.get('t')} "
                    f"SYMMETRY DUPLICATE of candidate {duplicate_of}; PGL2 charts skipped",
                    flush=True,
                )
                result = {
                    "curve_id": None,
                    "parameter": cand.get("t"),
                    "raw_parameter": cand.get("raw_t"),
                    "status": "symmetry_duplicate",
                    "symmetry_duplicate": True,
                }
                results.append(result)
                print(f"[candidate done] {index}/{len(candidates)}", flush=True)
                continue
            try:
                result = _run_one(db, cand, args, rpinfo, index, len(candidates))
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                result = {
                    "curve_id": cand.get("curve_id"),
                    "parameter": cand.get("t"),
                    "status": "unexpected_error",
                    "error": repr(exc),
                }
                curve_id = cand.get("curve_id")
                if curve_id is not None:
                    update_curve(db, int(curve_id), status="error", error=repr(exc))
                    log_event(db, int(curve_id), "error", f"Mestre PGL2 search: {exc!r}")
                print("    UNEXPECTED ERROR:", repr(exc), flush=True)
            results.append(result)
            print(f"[candidate done] {index}/{len(candidates)}", flush=True)

        aggregate = {
            "status": "MESTRE PGL2 COMPLETE",
            "family": family.name(),
            "family_spec": FAMILY_SPEC,
            "search_geometry": "pgl2",
            "search_mode": f"pgl2-{args.mode}",
            "chart_strategy": str(args.chart_strategy),
            "candidates_planned": len(candidates),
            "candidates_completed": len(results),
            "symmetry_duplicates_skipped": sum(bool(r.get("symmetry_duplicate")) for r in results),
            "charts_searched": sum(int(r.get("charts_searched") or 0) for r in results),
            "promoted_charts": sum(int(r.get("promoted_charts") or 0) for r in results),
            "banded_rational": any(bool(r.get("banded_rational")) for r in results),
            "charts_base": sum(int(r.get("charts_base") or 0) for r in results),
            "charts_subgroup": sum(int(r.get("charts_subgroup") or 0) for r in results),
            "charts_free": sum(int(r.get("charts_free") or 0) for r in results),
            "charts_exploratory": sum(int(r.get("charts_exploratory") or 0) for r in results),
            "exploratory_anchor_fibres": sum(int(r.get("exploratory_anchor_fibres") or 0) for r in results),
            "exploratory_anchor_available": sum(int(r.get("exploratory_anchor_available") or 0) for r in results),
            "exploratory_band_counts": _merge_count_maps(results, "exploratory_band_counts"),
            "new_fiber_band_counts": _merge_count_maps(results, "new_fiber_band_counts"),
            "discovered_anchor_fibres": sum(int(r.get("discovered_anchor_fibres") or 0) for r in results),
            "quartic_stages_checked": sum(int(r.get("quartic_stages_checked") or 0) for r in results),
            "new_native_fibers": sum(int(r.get("new_native_fibers") or 0) for r in results),
            "mapped_extra_points": sum(int(r.get("mapped_extra_points") or 0) for r in results),
            "rank_growth_curves": sum(1 for r in results if int(r.get("exact_rank_growth") or 0) > 0),
            "best_rigorous_lower": max([0, *[int(r.get("best_rigorous_lower") or 0) for r in results]]),
            "best_screened_rank": max([0, *[int(r.get("best_screened_rank") or 0) for r in results]]),
            "ratpoints_timeouts": sum(int(r.get("ratpoints_timeouts") or 0) for r in results),
            "subgroup_candidates_screened": sum(int(r.get("subgroup_candidates_screened") or 0) for r in results),
            "numerically_novel_candidates": sum(int(r.get("numerically_novel_candidates") or 0) for r in results),
            "exact_candidate_attempts": sum(int(r.get("exact_candidate_attempts") or 0) for r in results),
            "exact_dependent": sum(int(r.get("exact_dependent") or 0) for r in results),
            "exact_inconclusive": sum(int(r.get("exact_inconclusive") or 0) for r in results),
            "exact_scheduled_novel": sum(int(r.get("exact_scheduled_novel") or 0) for r in results),
            "exact_scheduled_controls": sum(int(r.get("exact_scheduled_controls") or 0) for r in results),
            "exact_skipped_non_novel": sum(int(r.get("exact_skipped_non_novel") or 0) for r in results),
            "proof_note": (
                "PGL2 transforms and inverse-mapped quartic/elliptic points are exact; subgroup residuals are numerical "
                "scheduling screens only; best_rigorous_lower changes only after the exact quadratic-character certificate succeeds"
            ),
        }
        print(RESULT_MARKER + json.dumps(aggregate, sort_keys=True), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
