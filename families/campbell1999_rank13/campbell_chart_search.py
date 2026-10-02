"""Exact PGL2-chart search for the Campbell 1999 rank-13 sextuple family.

The native Campbell quartic is very effective at producing rational points, but
once a specialization has a substantial certified Mordell--Weil subgroup it
can become biased toward repeatedly exposing combinations of that subgroup.
This adapter changes *search coordinates*, not the curve:

    native C_t : y^2 = f_t(x)
        x = (A u + B)/(C u + D)
        v = (C u + D)^2 y
    chart C_t^M : v^2 = (C u + D)^4 f_t((A u + B)/(C u + D)).

Charts are selected by an operator-visible strategy. Base charts use triples
of the twelve exact Campbell base-fibre abscissas; subgroup-informed charts mix
those anchors with exact non-base native fibres discovered in prior searches;
free charts use small primitive PGL2(Q) matrices independent of known points;
and hybrid mode interleaves the three sources adaptively. Every ratpoints hit
is inverse mapped exactly to the native quartic and checked there before it is
mapped to E(Q).

The proof boundary is unchanged from ``campbell_quartic_search``: Neron--Tate
projection residuals only schedule work.  A rigorous lower bound changes only
after the exact quadratic-character independence certificate succeeds.
"""

from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from campbell_runtime import family

from sage.all import QQ

from rank42.timeouts import StageTimeout, hard_timeout
from rank42.db import connect, get_curve, get_curve_by_key, log_event, upsert_curve, update_curve
from rank42.lattice_store import store_covering, update_covering
from campbell_quartic_search import (
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
    _validate_candidate_identity,
)
from rank42.mobius_quartic import build_chart_plan, evaluate, inverse_point, rational_height_bits
from rank42.quartic_store import create_or_get_search, finish_search, mark_running, store_points
from rank42.novelty import check_icarm_on_write
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
            "source": "campbell_sextuple_pgl2_chart",
            "family_spec": FAMILY_SPEC,
            "historical_generic_rank_lower": int(family.historical_generic_rank_lower),
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
        hole_label=f"campbell-pgl2-{chart_rank}-{pass_name}",
        coefficients=norm.rational_coefficients,
        integer_coefficients=norm.integer_coefficients,
        y_scale=norm.y_scale,
        degree=norm.degree,
        height_bound=height,
        denominator_low=dl,
        denominator_high=du,
        extra_args=args.extra_arg,
        metadata={
            "source": "campbell_sextuple_pgl2_chart",
            "family_spec": FAMILY_SPEC,
            "score": score,
            "chart_rank": int(chart_rank),
            "chart_strategy_source": str(chart.source),
            "chart": chart.as_metadata(),
            "search_pass": pass_name,
        },
    )

    if search["status"] == "done" and not args.force:
        print(
            f"    [campbell stage] mode=chart-{pass_name} H={height} "
            f"reuse search #{search['id']} points={search['point_count'] or 0}",
            flush=True,
        )
    else:
        mark_running(db, search["id"], executable=rpinfo["executable"])
        started = time.monotonic()
        try:
            result = run_ratpoints(
                norm.rational_coefficients,
                height,
                executable=rpinfo["executable"],
                timeout=args.timeout,
                denominator_low=dl,
                denominator_high=du,
                extra_args=args.extra_arg,
            )
        except RatpointsTimeout as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="timeout", runtime=runtime, error=str(exc))
            print(
                f"    [campbell stage] mode=chart-{pass_name} H={height} TIMEOUT",
                flush=True,
            )
            return search, [], "timeout"
        except RatpointsFailure as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="error", runtime=runtime, error=str(exc))
            print(
                f"    [campbell stage] mode=chart-{pass_name} H={height} ERROR {exc!r}",
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
            f"    [campbell stage] mode=chart-{pass_name} H={height} "
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
        if raw_x is None and source == "campbell_sextuple_native_quartic":
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


def parse_args():
    ap = argparse.ArgumentParser(
        description="Search exact PGL2 coordinate charts of the Campbell 1999 quartic."
    )
    ap.add_argument("--branch", choices=["c1","c2","c3","c4","c5","c6"], default=family.key)
    ap.add_argument("--db", default="rank42.db")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--id", type=int, help="target one stored Campbell curve id")
    src.add_argument("--parameter", help="target one rational t and create/reuse its DB row")
    src.add_argument("--input", help="Nagao candidate JSONL; accepts t or a,b")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--mode", choices=["integer", "rational", "both"], default="both")
    ap.add_argument("--charts", type=int, default=12, help="top exact PGL2 charts per specialization")
    ap.add_argument(
        "--chart-strategy", choices=["base", "subgroup", "free", "hybrid"], default="hybrid",
        help="PGL2 coordinate strategy; hybrid adaptively mixes base, discovered-fibre, and free charts",
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
        "--stages",
        type=_parse_stages,
        default=_parse_stages("1000,10000"),
        help="comma-separated ratpoints heights in chart coordinates",
    )
    ap.add_argument("--timeout", type=int, default=20, help="ratpoints timeout per chart/pass/stage")
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
    ap.add_argument("--construction-timeout", type=int, default=120, help="hard timeout for exact native Campbell curve/quartic construction per candidate")
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
    print(
        f"    cheap PGL2 scout setup ready in {time.monotonic()-setup_started:.3f}s; "
        "elliptic model deferred until a hit",
        flush=True,
    )
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
    for j, chart in enumerate(charts, 1):
        print(f"    [chart {j}/{len(charts)}]", flush=True)
        charts_searched += 1
        stop_pass = set()
        for pass_name, dl, du in _search_passes(args.mode):
            for height in args.stages:
                if pass_name in stop_pass:
                    break
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
                    stop_pass.add(pass_name)
                    continue
                if status == "error":
                    stage_errors += 1
                    stop_pass.add(pass_name)
                    continue
                for qrow in qrows:
                    mapped_native = inverse_point(chart, qrow["x"], qrow["y"])
                    if mapped_native is None:
                        continue
                    x, y = mapped_native
                    if y * y != evaluate(native_poly, x):
                        raise ArithmeticError("Campbell PGL2 inverse failed exact native-quartic check")
                    meta = json.loads(qrow["metadata_json"] or "{}")
                    meta.update(
                        {
                            "native_x": str(x),
                            "native_y": str(y),
                            "pgl2_chart": chart.as_metadata(),
                            "inverse_map_verified_exactly": True,
                        }
                    )
                    db.execute(
                        "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                        (json.dumps(meta, sort_keys=True), qrow["id"]),
                    )
                    db.commit()
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

    new_x = {hit["x"] for hit in native_hits.values() if hit["x"] not in known_x}
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
        "charts_searched": int(scout["charts_searched"]),
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
        raise ValueError("Campbell construction construction degenerates at t=0")
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
    print("    scouting exact Campbell PGL2 quartics first...", flush=True)
    try:
        scout = _scout_pgl2_quartics(
            db, curve_id=curve_id, param=param, score=score, t=t, args=args, rpinfo=rpinfo
        )
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Campbell PGL2 scout failed: {exc!r}")
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
    print("    hit found; materializing exact Campbell elliptic model + 13 displayed section candidates...", flush=True)
    construction_started = time.monotonic()
    try:
        with hard_timeout(args.construction_timeout, "Campbell exact native construction"):
            bundle = family.direct_search_bundle(t)
    except StageTimeout as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "timeout", f"Campbell exact construction timeout: {exc}")
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
        log_event(db, curve_id, "error", f"Campbell PGL2 model construction failed: {exc!r}")
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
    icarm=check_icarm_on_write(db,curve_id,E)
    if icarm.get('status') == 'known':
        print(f"    ICARM match: #{icarm.get('source_id')}", flush=True)
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
            "stored Campbell curve model differs from the current deterministic family model while rigorous generators exist; "
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
        basis_candidates = [list(x) for x in (bundle.get("basis_candidates") or [family_basis])]
        selected_basis = family_basis
        for basis_index, candidate_basis in enumerate(basis_candidates, 1):
            rigorous_basis, baseline_cert = _ensure_baseline_certificate(
                db, row, E, candidate_basis, args.certificate_timeout
            )
            selected_basis = candidate_basis
            if rigorous_basis:
                break
            if str((baseline_cert or {}).get("status")) != "dependent":
                break
            if basis_index < len(basis_candidates):
                print(
                    f"    [exact baseline] Campbell infinity choice {basis_index} was dependent; "
                    "trying the alternate exact infinity basis",
                    flush=True,
                )
        family_basis = list(selected_basis)
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
                "source": "campbell_pgl2_ratpoints",
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
                f"    [campbell novelty] screened={len(ranked)} numerical_new={numerical_new} "
                f"best_rel_residual={best_rel:.6g}",
                flush=True,
            )
        else:
            print("    [campbell novelty] numerical subgroup screen unavailable", flush=True)

    ranked_keys = {_point_key(rec["point"]): rec for rec in ranked}
    for rec in mapped:
        key = _point_key(rec["point"])
        source_rec = ranked_keys.get(key, rec)
        source_rec.setdefault("source", "campbell_pgl2_ratpoints")
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
        "charts_searched": charts_searched,
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
                _validate_candidate_identity(raw)
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

        print("RANK HUNTER CAMPBELL PGL2-CHART SEARCH")
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
        print("height stages       =", ",".join(str(x) for x in args.stages))
        print("timeout/chart-stage =", args.timeout, "s")
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
                    log_event(db, int(curve_id), "error", f"Campbell PGL2 search: {exc!r}")
                print("    UNEXPECTED ERROR:", repr(exc), flush=True)
            results.append(result)
            print(f"[candidate done] {index}/{len(candidates)}", flush=True)

        aggregate = {
            "status": "CAMPBELL PGL2 COMPLETE",
            "family": family.name(),
            "family_spec": FAMILY_SPEC,
            "search_geometry": "pgl2",
            "search_mode": f"pgl2-{args.mode}",
            "chart_strategy": str(args.chart_strategy),
            "candidates_planned": len(candidates),
            "candidates_completed": len(results),
            "symmetry_duplicates_skipped": sum(bool(r.get("symmetry_duplicate")) for r in results),
            "charts_searched": sum(int(r.get("charts_searched") or 0) for r in results),
            "charts_base": sum(int(r.get("charts_base") or 0) for r in results),
            "charts_subgroup": sum(int(r.get("charts_subgroup") or 0) for r in results),
            "charts_free": sum(int(r.get("charts_free") or 0) for r in results),
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
