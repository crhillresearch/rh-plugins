"""Native-quartic point search for the Fermigier--Mestre exact rank-12 family.

The family module supplies an exact normalized genus-one quartic

    C_t : y^2 = r_t(x)

with thirteen known rational points and an exact map to a Weierstrass model.
This adapter turns that mathematical API into a persistent Rank Hunter search:

    Nagao candidate / t
        -> native quartic ratpoints search
        -> exact removal of known base fibres
        -> exact map to E(Q)
        -> numerical subgroup-novelty ordering
        -> exact quadratic-character independence certificate.

The numerical Neron--Tate step is a screen only.  The curve's rigorous lower
bound is changed only when ``rank42.exact_lb`` certifies the supplied rational
points independent modulo torsion.

The search engine supports integer and rational quartic abscissas. The plugin UI
defaults to PGL2/hybrid search because subgroup-aware coordinate diversity is preferred.  ``rational``
searches all denominators allowed by ratpoints; ``both`` performs an integer
pass first and then a non-integral pass (denominator >=2), preserving the cheap
positive-control path without excluding rational-x discoveries.
"""

from __future__ import annotations

import argparse
import json
import time
from fractions import Fraction
from pathlib import Path

from sage.all import QQ

from rank42.timeouts import StageTimeout, hard_timeout
from rank42.db import connect, get_curve, get_curve_by_key, log_event, upsert_curve, update_curve
from rank42.exact_lb import ExactCertificateFailure, ExactCertificateTimeout, run_exact_certificate
if __package__:
    from . import family
else:
    import family
from rank42.height_bounded import HeightScreenFailure, HeightScreenTimeout, run_height_screen
from rank42.general_hunt_core import canonical_affine_key, parse_height_stages
from rank42.lattice_store import store_covering, store_extra_point, update_covering
from rank42.quartic_store import create_or_get_search, finish_search, mark_running, store_points
from rank42.ratpoints import (
    RatpointsFailure,
    RatpointsNotFound,
    RatpointsTimeout,
    normalize_polynomial,
    probe_version,
    run_ratpoints,
)
if __package__:
    from .subgroup_focus import projection_residuals, rank_novelty, spread_points
else:
    from subgroup_focus import projection_residuals, rank_novelty, spread_points


RESULT_MARKER = "RANK42_MESTRE_SEARCH_RESULT="
FAMILY_SPEC = "plugins.fermigier_rank12_exact.family"


def _fq(value):
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _point_key(P):
    return canonical_affine_key(_fq(P[0]), _fq(P[1]))


def _parse_stages(text):
    try:
        return parse_height_stages(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _candidate_rows(path, limit):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"candidate line {line_no} is not a JSON object")
            rows.append(value)
    rows.sort(key=lambda row: float(row.get("score", 0.0)), reverse=True)
    return rows[: int(limit)]


def _raw_row_parameter(row):
    if row.get("t") is not None:
        return QQ(str(row["t"]))
    if row.get("a") is None or row.get("b") is None:
        raise ValueError("candidate row requires either t or both a,b")
    return QQ(row["a"]) / QQ(row["b"])


def _canonical_parameter(value):
    return family.canonical_parameter(QQ(value))


def _row_parameter(row):
    return str(_canonical_parameter(_raw_row_parameter(row)))


def _candidate_from_id(db, curve_id):
    row = get_curve(db, int(curve_id))
    if row is None:
        raise SystemExit(f"curve #{curve_id} not found")
    if row["family"] != family.name():
        raise SystemExit(
            f"curve #{curve_id} belongs to {row['family']!r}, not {family.name()!r}"
        )
    return {
        "curve_id": int(row["id"]),
        "t": str(row["parameter"]),
        "score": float(row["score"] or 0.0),
    }


def _search_passes(mode):
    mode = str(mode)
    if mode == "integer":
        return [("integer", 1, 1)]
    if mode == "rational":
        return [("rational", None, None)]
    if mode == "both":
        return [("integer", 1, 1), ("nonintegral", 2, None)]
    raise ValueError(f"unknown Fermigier search mode: {mode}")


def _covering_payload(curve_id, bundle, height, search_id, pass_name):
    return {
        "schema": "rank42.covering.v1",
        "curve_id": int(curve_id),
        "quartic": {
            "coefficients": [str(x) for x in bundle["quartic_coefficients"]],
            "height": int(height),
        },
        "map": family.covering_map_expressions(bundle),
        "metadata": {
            "source": "fermigier_rank12_native_quartic",
            "family_spec": FAMILY_SPEC,
            "declared_generic_rank": int(family.generic_rank),
            "quartic_search_id": int(search_id),
            "search_pass": str(pass_name),
        },
    }


def _load_stored_rigorous_basis(E, row):
    """Reconstruct only the witness count already stored as a rigorous lower bound."""
    lower = int(row["descent_lower"] or 0)
    if lower <= 0:
        return []
    try:
        raw = json.loads(row["generators_json"] or "[]")
    except Exception:
        return []
    points = []
    seen = set()
    for xy in raw:
        if not isinstance(xy, (list, tuple)) or len(xy) < 2:
            continue
        try:
            P = E(QQ(str(xy[0])), QQ(str(xy[1])))
        except Exception:
            continue
        if P.is_zero():
            continue
        key = _point_key(P)
        if key in seen:
            continue
        seen.add(key)
        points.append(P)
        if len(points) >= lower:
            break
    return points if len(points) >= lower else []


def _store_rigorous_basis(db, row, E, basis, message):
    rigorous = len(basis)
    current = get_curve(db, int(row["id"])) or row
    previous = max(int(current["descent_lower"] or 0), int(current["exact_rank"] or 0))
    if rigorous <= previous:
        return previous
    update_curve(
        db,
        int(row["id"]),
        descent_lower=rigorous,
        generators_json=json.dumps([[str(P[0]), str(P[1])] for P in basis]),
        status="proven_lower" if current["exact_rank"] is None else "exact",
        error=None,
    )
    log_event(db, int(row["id"]), "best", message)
    return rigorous


def _certify(points, E, timeout):
    return run_exact_certificate(
        [str(a) for a in E.a_invariants()],
        [[str(P[0]), str(P[1])] for P in points],
        timeout=int(timeout),
    )


def _ensure_baseline_certificate(db, row, E, family_basis, timeout):
    stored = _load_stored_rigorous_basis(E, row)
    if stored:
        return stored, {
            "status": "stored_rigorous_basis",
            "independent": True,
            "rank_lower_bound": len(stored),
        }

    print(
        f"    [exact baseline] certifying {len(family_basis)} displayed Mestre sections "
        f"(timeout {int(timeout)}s)...",
        flush=True,
    )
    try:
        cert = _certify(family_basis, E, timeout)
    except ExactCertificateTimeout as exc:
        log_event(db, int(row["id"]), "warn", f"Fermigier baseline exact certificate timed out: {exc}")
        print("        TIMEOUT -> search continues; no baseline rank claim stored", flush=True)
        return [], {"status": "timeout", "independent": False, "error": str(exc)}
    except ExactCertificateFailure as exc:
        log_event(db, int(row["id"]), "warn", f"Fermigier baseline exact certificate failed: {exc}")
        print("        ERROR -> search continues; no baseline rank claim stored", flush=True)
        return [], {"status": "error", "independent": False, "error": str(exc)}

    status = str(cert.get("status") or "unknown")
    print(f"        status={status} lower={cert.get('rank_lower_bound')}", flush=True)
    if cert.get("independent"):
        _store_rigorous_basis(
            db,
            row,
            E,
            family_basis,
            f"Fermigier exact certificate proves {len(family_basis)} specialized section points independent",
        )
        return list(family_basis), cert

    if status == "dependent":
        log_event(
            db,
            int(row["id"]),
            "error",
            "Fermigier displayed specialization section set was exactly certified dependent; generic-rank metadata was not promoted",
        )
    return [], cert


def _search_stage(db, *, curve_id, param, score, coeffs, height, pass_name, dl, du, args, rpinfo):
    norm = normalize_polynomial(coeffs)
    search = create_or_get_search(
        db,
        curve_id=curve_id,
        family=family.name(),
        parameter=param,
        hole_label=f"mestre-native-{pass_name}",
        coefficients=norm.rational_coefficients,
        integer_coefficients=norm.integer_coefficients,
        y_scale=norm.y_scale,
        degree=norm.degree,
        height_bound=height,
        denominator_low=dl,
        denominator_high=du,
        extra_args=args.extra_arg,
        metadata={
            "source": "fermigier_rank12_native_quartic",
            "family_spec": FAMILY_SPEC,
            "score": score,
            "search_pass": pass_name,
            "declared_generic_rank": int(family.generic_rank),
        },
    )

    if search["status"] == "done" and not args.force:
        print(
            f"    [mestre stage] mode={pass_name} H={height} reuse search #{search['id']} "
            f"points={search['point_count'] or 0}",
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
            print(f"    [mestre stage] mode={pass_name} H={height} TIMEOUT", flush=True)
            return search, [], "timeout"
        except RatpointsFailure as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="error", runtime=runtime, error=str(exc))
            print(f"    [mestre stage] mode={pass_name} H={height} ERROR {exc!r}", flush=True)
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
            f"    [mestre stage] mode={pass_name} H={height} points={len(result['points'])} "
            f"runtime={result['runtime']:.3f}",
            flush=True,
        )

    rows = db.execute(
        "SELECT * FROM quartic_points WHERE search_id=? ORDER BY id",
        (search["id"],),
    ).fetchall()
    return search, rows, "done"


def _screen_candidates(E, basis, records, args):
    """Numerically rank exact mapped points by Neron--Tate subgroup residual."""
    if not records:
        return [], []
    selected_points = spread_points([rec["point"] for rec in records], int(args.subgroup_scan))
    by_key = {_point_key(rec["point"]): rec for rec in records}
    selected = [by_key[_point_key(P)] for P in selected_points]

    ranked = []
    failures = []
    chunk_size = max(1, int(args.subgroup_chunk))
    for start in range(0, len(selected), chunk_size):
        chunk = selected[start : start + chunk_size]
        points = list(basis) + [rec["point"] for rec in chunk]
        try:
            screen = run_height_screen(
                E,
                points,
                precision=int(args.precision),
                timeout=int(args.height_timeout),
            )
            residuals = projection_residuals(screen.get("gram") or [], len(basis))
        except HeightScreenTimeout:
            failures.append({"start": start, "count": len(chunk), "status": "timeout"})
            print(f"    [mestre subgroup] chunk={start} count={len(chunk)} TIMEOUT", flush=True)
            continue
        except (HeightScreenFailure, ValueError) as exc:
            failures.append({"start": start, "count": len(chunk), "status": "error", "error": repr(exc)})
            print(f"    [mestre subgroup] chunk={start} count={len(chunk)} ERROR {exc!r}", flush=True)
            continue
        gram = screen.get("gram") or []
        for candidate_offset, (rec, novelty) in enumerate(zip(chunk, residuals)):
            out = dict(rec)
            out.update(novelty)
            out["x"] = str(rec["point"][0])
            out["y"] = str(rec["point"][1])
            ranked.append(out)
    return rank_novelty(ranked), failures


def _record_extra(db, rec, *, before, numerical_new, screen_after, exact_status=None, exact_error=None):
    novelty = rec.get("relative_residual")
    store_extra_point(
        db,
        covering_id=rec["covering_id"],
        quartic_point_id=rec["qrow_id"],
        curve_id=rec["curve_id"],
        x=rec["point"][0],
        y=rec["point"][1],
        exact_verified=True,
        independence_screen=bool(numerical_new),
        basis_count_before=int(before),
        basis_count_after=int(screen_after),
        determinant=None,
        min_eigenvalue=None,
        metadata={
            "source": rec.get("source", "mestre_native_ratpoints"),
            "chart_strategy_source": rec.get("chart_strategy_source"),
            "family_spec": FAMILY_SPEC,
            "precision_bits": rec.get("precision_bits"),
            "projection_residual": rec.get("residual"),
            "relative_projection_residual": novelty,
            "screen_only": True,
            "exact_status": exact_status,
            "exact_error": exact_error,
            "proof_note": (
                "exact quartic and elliptic point; Neron-Tate subgroup residual is numerical only; "
                "rank changes only after exact quadratic-character certification"
            ),
        },
    )


def _select_exact_candidates(records, args):
    """Choose exact-certificate work without wasting it on zero-residual points.

    If a numerical subgroup screen succeeded, only candidates above the
    declared novelty threshold are normal proof targets.  A small bounded
    number of below-threshold points may still be retained as diagnostic exact
    controls.  If the numerical screen was unavailable altogether, fall back
    to a deterministic spread so floating-point failure cannot block proof.
    """
    limit = max(0, int(args.exact_candidates))
    if limit <= 0 or not records:
        return [], {"mode": "disabled", "novel": 0, "controls": 0, "unscreened": 0, "skipped_non_novel": 0}

    screened = [rec for rec in records if rec.get("relative_residual") is not None]
    if not screened:
        selected_points = spread_points([rec["point"] for rec in records], limit)
        lookup = {_point_key(rec["point"]): rec for rec in records}
        ordered = [lookup[_point_key(P)] for P in selected_points]
        return ordered, {
            "mode": "screen_unavailable",
            "novel": 0,
            "controls": 0,
            "unscreened": len(records),
            "skipped_non_novel": 0,
        }

    tol = float(args.novelty_rel_tol)
    novel = [rec for rec in screened if float(rec.get("relative_residual") or 0.0) > tol]
    non_novel = [rec for rec in screened if float(rec.get("relative_residual") or 0.0) <= tol]
    selected = list(novel[:limit])

    control_budget = max(0, int(getattr(args, "exact_control_candidates", 1)))
    remaining = max(0, limit - len(selected))
    controls = []
    if remaining and control_budget and non_novel:
        take = min(remaining, control_budget, len(non_novel))
        control_points = spread_points([rec["point"] for rec in non_novel], take)
        lookup = {_point_key(rec["point"]): rec for rec in non_novel}
        controls = [lookup[_point_key(P)] for P in control_points]
        selected.extend(controls)

    return selected, {
        "mode": "screened",
        "novel": min(len(novel), limit),
        "controls": len(controls),
        "unscreened": sum(rec.get("relative_residual") is None for rec in records),
        "skipped_non_novel": max(0, len(non_novel) - len(controls)),
    }


def _try_exact_growth(db, row, E, seed_basis, records, args):
    """Use numerical order only for scheduling; exact certificate decides growth."""
    basis = list(seed_basis)
    exact_attempts = 0
    exact_dependent = 0
    exact_inconclusive = 0
    exact_errors = 0
    growth = 0
    limit = max(0, int(args.exact_candidates))
    ordered, scheduling = _select_exact_candidates(records, args)
    if records and limit > 0:
        print(
            "    [mestre exact schedule] "
            f"mode={scheduling['mode']} novel={scheduling['novel']} "
            f"controls={scheduling['controls']} unscreened={scheduling['unscreened']} "
            f"skipped_non_novel={scheduling['skipped_non_novel']}",
            flush=True,
        )

    for rec in ordered[:limit]:
        P = rec["point"]
        trial = list(basis) + [P]
        exact_attempts += 1
        exact_status = None
        exact_error = None
        try:
            cert = _certify(trial, E, args.certificate_timeout)
            exact_status = str(cert.get("status") or "unknown")
        except ExactCertificateTimeout as exc:
            cert = None
            exact_status = "timeout"
            exact_error = str(exc)
            exact_inconclusive += 1
        except ExactCertificateFailure as exc:
            cert = None
            exact_status = "error"
            exact_error = str(exc)
            exact_errors += 1

        rel = rec.get("relative_residual")
        rel_text = f" rel_residual={float(rel):.6g}" if rel is not None else ""
        print(
            f"    [mestre exact] candidate={exact_attempts}/{limit}{rel_text} status={exact_status}",
            flush=True,
        )

        numerical_new = bool(
            rel is not None and float(rel) > float(args.novelty_rel_tol)
        )
        before = len(basis)
        if cert is not None and cert.get("independent"):
            basis = trial
            growth += 1
            rigorous = _store_rigorous_basis(
                db,
                row,
                E,
                basis,
                f"Fermigier native-quartic exact certificate improves rigorous lower bound to {len(basis)}",
            )
            print(
                f"    [mestre hit] curve #{int(row['id'])} rigorous_lower={rigorous} points={len(basis)}",
                flush=True,
            )
        elif cert is not None and exact_status == "dependent":
            exact_dependent += 1
        elif cert is not None:
            exact_inconclusive += 1

        _record_extra(
            db,
            rec,
            before=before,
            numerical_new=numerical_new,
            screen_after=(before + 1 if numerical_new else before),
            exact_status=exact_status,
            exact_error=exact_error,
        )

    return basis, {
        "attempts": exact_attempts,
        "dependent": exact_dependent,
        "inconclusive": exact_inconclusive,
        "errors": exact_errors,
        "growth": growth,
        "scheduled_novel": int(scheduling.get("novel", 0)),
        "scheduled_controls": int(scheduling.get("controls", 0)),
        "skipped_non_novel": int(scheduling.get("skipped_non_novel", 0)),
    }


def parse_args():
    ap = argparse.ArgumentParser(
        description="Search the native Fermigier--Mestre rank-12 quartic for extra rational points."
    )
    ap.add_argument("--db", default="rank42.db")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--id", type=int, help="target one stored Fermigier curve id")
    src.add_argument("--parameter", help="target one rational parameter t and create/reuse its DB row")
    src.add_argument("--input", help="Nagao candidate JSONL; accepts t or a,b")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--mode", choices=["integer", "rational", "both"], default="integer")
    ap.add_argument("--stages", type=_parse_stages, default=_parse_stages("1000,10000,100000"))
    ap.add_argument("--timeout", type=int, default=15, help="ratpoints timeout per pass/stage")
    ap.add_argument("--ratpoints")
    ap.add_argument("--extra-arg", action="append", default=[])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--include-known-fibers", action="store_true",
                    help="map the opposite signs over the twelve known base fibres as an exact involution control")
    ap.add_argument("--precision", type=int, default=192)
    ap.add_argument("--height-timeout", type=int, default=20)
    ap.add_argument("--subgroup-scan", type=int, default=128)
    ap.add_argument("--subgroup-chunk", type=int, default=24)
    ap.add_argument("--exact-candidates", type=int, default=8)
    ap.add_argument(
        "--exact-control-candidates",
        type=int,
        default=1,
        help="below-novelty exact controls to retain when a numerical subgroup screen succeeds",
    )
    ap.add_argument("--construction-timeout", type=int, default=120, help="hard timeout for exact native Fermigier curve/quartic construction per candidate")
    ap.add_argument("--certificate-timeout", type=int, default=60)
    ap.add_argument("--novelty-rel-tol", type=float, default=1e-8)
    ap.add_argument("--skip-baseline-certificate", action="store_true",
                    help="discovery-only mode: do not spend an exact certificate on the eleven displayed sections before searching")
    return ap.parse_args()



def _scout_native_quartic(db, *, curve_id, param, score, t, args, rpinfo):
    """Search the exact native quartic before materializing E(Q).

    This is the broad-search fast path.  It uses only the normalized quartic
    coefficients and the twelve known native fibres.  The expensive elliptic
    model, generic sections, height data and exact certificate machinery are
    deliberately deferred until ratpoints finds a genuinely new native fibre.
    """
    setup_started = time.monotonic()
    coeffs = list(family.quartic_search_coefficients(t))
    known_native = family.native_quartic_known_points(t)
    known_x = {_fq(x) for x, _ in known_native}
    print(
        f"    cheap native quartic scout ready in {time.monotonic()-setup_started:.3f}s; "
        "elliptic model deferred until a hit",
        flush=True,
    )

    native_hits = {}
    timeouts = 0
    stage_errors = 0
    stage_count = 0
    stop_pass = set()
    for pass_name, dl, du in _search_passes(args.mode):
        for height in args.stages:
            if pass_name in stop_pass:
                break
            stage_count += 1
            search, qrows, status = _search_stage(
                db,
                curve_id=curve_id,
                param=param,
                score=score,
                coeffs=coeffs,
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
                x = _fq(qrow["x"])
                y = _fq(qrow["y"])
                if not args.include_known_fibers and x in known_x:
                    continue
                native_hits.setdefault(
                    (x, y),
                    {
                        "qrow": qrow,
                        "search": search,
                        "height": int(height),
                        "pass_name": pass_name,
                        "x": x,
                        "y": y,
                    },
                )

    new_x = {hit["x"] for hit in native_hits.values() if hit["x"] not in known_x}
    return {
        "coeffs": coeffs,
        "known_native": known_native,
        "known_x": known_x,
        "native_hits": native_hits,
        "new_x": new_x,
        "timeouts": timeouts,
        "stage_errors": stage_errors,
        "stage_count": stage_count,
    }


def _negative_scout_result(db, *, curve_id, param, started, args, scout):
    row = get_curve(db, curve_id)
    rigorous = max(int(row["descent_lower"] or 0), int(row["exact_rank"] or 0))
    if row["exact_rank"] is None:
        update_curve(db, curve_id, status="extra_done", error=None)
    print("    no new native quartic x-fibres -> no elliptic model needed", flush=True)
    return {
        "curve_id": curve_id,
        "parameter": param,
        "status": "extra_done",
        "current_lower_before": rigorous,
        "best_rigorous_lower": rigorous,
        "baseline_certificate_status": "deferred_no_hit",
        "search_geometry": "native",
        "search_mode": str(args.mode),
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
    print("    scouting exact native Mestre quartic first...", flush=True)
    try:
        scout = _scout_native_quartic(
            db, curve_id=curve_id, param=param, score=score, t=t, args=args, rpinfo=rpinfo
        )
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Fermigier native scout failed: {exc!r}")
        print("    SCOUT ERROR:", repr(exc), flush=True)
        return {
            "curve_id": curve_id,
            "parameter": param,
            "status": "scout_error",
            "error": repr(exc),
            "runtime_seconds": time.monotonic() - started,
        }

    new_x = set(scout["new_x"])
    if not new_x and not args.include_known_fibers:
        return _negative_scout_result(
            db, curve_id=curve_id, param=param, started=started, args=args, scout=scout
        )

    if new_x:
        print(f"    NEW NATIVE QUARTIC HIT(S): {len(new_x)} new x-fibre(s)", flush=True)
    print("    hit found; materializing exact Fermigier elliptic model + 12 sections...", flush=True)
    construction_started = time.monotonic()
    try:
        with hard_timeout(args.construction_timeout, "Fermigier exact native construction"):
            bundle = family.direct_search_bundle(t)
    except StageTimeout as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "timeout", f"Fermigier exact construction timeout: {exc}")
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
        log_event(db, curve_id, "error", f"Mestre model construction failed: {exc!r}")
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
    coeffs = list(scout["coeffs"])
    known_native = list(scout["known_native"])
    known_x = set(scout["known_x"])

    row = get_curve(db, curve_id)
    stored_ainvs = None
    try:
        stored_ainvs = json.loads(row["a_invariants_json"] or "null")
    except Exception:
        stored_ainvs = None
    current_ainvs = [str(a) for a in E.a_invariants()]
    if stored_ainvs and [str(x) for x in stored_ainvs] != current_ainvs and int(row["descent_lower"] or 0) > 0:
        msg = (
            "stored Fermigier curve model differs from the current deterministic family model while rigorous generators exist; "
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

    # Numerical screening may still use the displayed 12-section set if its
    # exact certificate timed out. Exact rank promotion never relies on that.
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

    # The cheap scout already performed every ratpoints stage exactly once.
    native_hits = dict(scout["native_hits"])
    timeouts = int(scout["timeouts"])
    stage_errors = int(scout["stage_errors"])
    stage_count = int(scout["stage_count"])
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
                hit["height"],
                hit["search"]["id"],
                hit["pass_name"],
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
                "precision_bits": int(args.precision),
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

    # Preserve every exact mapped point in the unified point ledger before the
    # bounded exact-certificate budget is applied. Exact attempts below upsert
    # richer status onto the same scientific record.
    ranked_keys = {_point_key(rec["point"]): rec for rec in ranked}
    for rec in mapped:
        key = _point_key(rec["point"])
        source_rec = ranked_keys.get(key, rec)
        rel = source_rec.get("relative_residual")
        numerical_new = bool(
            rel is not None and float(rel) > float(args.novelty_rel_tol)
        )
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
    exact_basis, exact_counts = _try_exact_growth(
        db,
        row,
        E,
        exact_seed_basis,
        exact_order,
        args,
    ) if mapped else (exact_seed_basis, {"attempts": 0, "dependent": 0, "inconclusive": 0, "errors": 0, "growth": 0, "scheduled_novel": 0, "scheduled_controls": 0, "skipped_non_novel": 0})

    final_row = get_curve(db, curve_id)
    rigorous_after = max(int(final_row["descent_lower"] or 0), int(final_row["exact_rank"] or 0))
    best_screened = len(screen_basis)
    if ranked and any(float(rec.get("relative_residual", 0.0)) > float(args.novelty_rel_tol) for rec in ranked):
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
        "search_mode": args.mode,
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
                if spec and spec not in {FAMILY_SPEC, "fermigier_rank12_exact"}:
                    raise SystemExit(
                        f"candidate family_spec {spec!r} is not the Fermigier rank-12 adapter"
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

        print("RANK HUNTER MESTRE NATIVE-QUARTIC SEARCH")
        print("=" * 72)
        print("family              =", family.name())
        print("parameter symmetry  = t ~ -t (candidate pools canonicalized)")
        print("ratpoints           =", rpinfo["executable"])
        print("ratpoints version   =", rpinfo["version"] or "unknown")
        print("candidates          =", len(candidates))
        print("search mode         =", args.mode)
        print("height stages       =", ",".join(str(x) for x in args.stages))
        print("timeout/pass-stage  =", args.timeout, "s")
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
                    f"SYMMETRY DUPLICATE of candidate {duplicate_of}; native quartic skipped",
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
                    log_event(db, int(curve_id), "error", f"Fermigier native search: {exc!r}")
                print("    UNEXPECTED ERROR:", repr(exc), flush=True)
            results.append(result)
            print(f"[candidate done] {index}/{len(candidates)}", flush=True)

        aggregate = {
            "status": "MESTRE COMPLETE",
            "family": family.name(),
            "family_spec": FAMILY_SPEC,
            "candidates_planned": len(candidates),
            "candidates_completed": len(results),
            "symmetry_duplicates_skipped": sum(bool(r.get("symmetry_duplicate")) for r in results),
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
            "search_mode": args.mode,
            "proof_note": (
                "quartic/elliptic points are exact; subgroup residuals are numerical scheduling screens only; "
                "best_rigorous_lower changes only after the exact quadratic-character certificate succeeds"
            ),
        }
        print(RESULT_MARKER + json.dumps(aggregate, sort_keys=True), flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
