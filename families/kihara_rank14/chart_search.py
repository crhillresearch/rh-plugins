"""Möbius-chart direct point scout for Kihara's rank-14 quartic family.

The native Kihara quartic can have enormous rational coordinates even at
moderate parameter height.  This scout chooses exact PGL2(Q) coordinate charts
from known section abscissas, sends three known x-values to 0, infinity, 1,
and lets ``ratpoints`` search the resulting equivalent quartics.

Every hit is inverted exactly to the native quartic before it is considered.
By default, points lying over one of the fourteen already-known native x-fibers
are ignored at the cheap stage.  This prevents the chart anchors themselves
from forcing the expensive 14-section Weierstrass/height machinery.  Use
``--include-known-fibers`` for an exhaustive check of the opposite signs too.
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

from rank42.db import (
    connect, get_curve, get_curve_by_key, log_event, upsert_curve, update_curve,
)
import family
from rank_claims import certify_specialized_sections, reconcile_specialization_lower
from rank42.height_bounded import HeightScreenFailure, HeightScreenTimeout, run_height_screen
from rank42.lattice_store import (
    lattice_key, store_covering, store_extra_point, store_lattice, update_covering,
)
from rank42.mobius_quartic import evaluate, inverse_point, rank_charts
from rank42.quartic_store import create_or_get_search, finish_search, mark_running, store_points
from rank42.ratpoints import (
    RatpointsFailure, RatpointsNotFound, RatpointsTimeout,
    normalize_polynomial, probe_version, run_ratpoints,
)


def _fq(x):
    return x if isinstance(x, Fraction) else Fraction(str(x))


def _canonical_point_key(P):
    Q = -P
    return min((QQ(P[0]), QQ(P[1])), (QQ(Q[0]), QQ(Q[1])))


def _parse_stages(text):
    vals = []
    for piece in str(text).split(","):
        piece = piece.strip()
        if not piece:
            continue
        value = int(piece)
        if value <= 0:
            raise argparse.ArgumentTypeError("stage heights must be positive")
        vals.append(value)
    vals = sorted(set(vals))
    if not vals:
        raise argparse.ArgumentTypeError("at least one stage height is required")
    return vals


def _candidate_rows(path, limit):
    rows = []
    with Path(path).open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)
    return rows[: int(limit)]


def _row_parameter(row):
    if row.get("t") is not None:
        return str(QQ(str(row["t"])))
    if row.get("a") is None or row.get("b") is None:
        raise ValueError("candidate row requires either t or both a,b")
    return str(QQ(row["a"]) / QQ(row["b"]))


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


def _covering_payload(curve_id, bundle, chart, height, search_id):
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
            "source": "kihara2001_mobius_chart",
            "historical_generic_rank_lower": 14,
            "generic_rank_claim_state": "sections_verified",
            "quartic_search_id": int(search_id),
            "chart": chart.as_metadata(),
        },
    }


def parse_args():
    ap = argparse.ArgumentParser(
        description="Search coordinate-reduced Kihara quartics for extra points."
    )
    ap.add_argument("--db", default="rank42.db")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--id", type=int, help="target one stored Kihara curve id")
    src.add_argument("--input", help="candidate JSONL; accepts t or a,b")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--charts", type=int, default=6,
                    help="number of top Mobius charts per specialization")
    ap.add_argument("--anchor-pool", type=int, default=12,
                    help="lowest-height known x-values used to form chart triples")
    ap.add_argument("--stages", type=_parse_stages, default=_parse_stages("1000,10000,100000"),
                    help="comma-separated ratpoints height stages")
    ap.add_argument("--timeout", type=int, default=20,
                    help="ratpoints timeout per chart/stage")
    ap.add_argument("--precision", type=int, default=128,
                    help="height precision only after a new native x is found")
    ap.add_argument("--height-timeout", type=int, default=60,
                    help="hard timeout for each post-hit Neron-Tate height screen")
    ap.add_argument("--certificate-timeout", type=int, default=120,
                    help="hard timeout for exact 14-section specialization certificate")
    ap.add_argument("--ratpoints")
    ap.add_argument("--extra-arg", action="append", default=[])
    ap.add_argument("--force", action="store_true", help="rerun completed chart searches")
    ap.add_argument("--include-known-fibers", action="store_true",
                    help="also map opposite signs over the 14 known native x-values")
    return ap.parse_args()


def _search_chart_stage(db, *, curve_id, param, score, chart, chart_rank, height,
                        args, rpinfo):
    norm = normalize_polynomial(chart.coefficients)
    search = create_or_get_search(
        db,
        curve_id=curve_id,
        family=family.name(),
        parameter=param,
        hole_label=f"kihara-mobius-{chart_rank}",
        coefficients=norm.rational_coefficients,
        integer_coefficients=norm.integer_coefficients,
        y_scale=norm.y_scale,
        degree=norm.degree,
        height_bound=height,
        extra_args=args.extra_arg,
        metadata={
            "source": "kihara2001_mobius_chart",
            "score": score,
            "chart_rank": chart_rank,
            "chart": chart.as_metadata(),
        },
    )

    if search["status"] == "done" and not args.force:
        print(
            f"      H={height:<9} reuse search #{search['id']} "
            f"({search['point_count'] or 0} point(s))"
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
                extra_args=args.extra_arg,
            )
        except RatpointsTimeout as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="timeout", runtime=runtime, error=str(exc))
            print(f"      H={height:<9} TIMEOUT -> skip higher stages for this chart")
            return search, [], True
        except RatpointsFailure as exc:
            runtime = time.monotonic() - started
            finish_search(db, search["id"], status="error", runtime=runtime, error=str(exc))
            print(f"      H={height:<9} ERROR -> skip chart")
            return search, [], True
        store_points(db, search["id"], result["points"])
        finish_search(
            db, search["id"], status="done", runtime=result["runtime"],
            point_count=len(result["points"]), error=None,
        )
        print(
            f"      H={height:<9} {len(result['points'])} point(s) "
            f"in {result['runtime']:.2f}s"
        )

    rows = db.execute(
        "SELECT * FROM quartic_points WHERE search_id=? ORDER BY id", (search["id"],)
    ).fetchall()
    return search, rows, False


def _point_json(P):
    return [str(P[0]), str(P[1])]


def _basis_height_screen(db, *, curve_id, E, basis, parameter, precision, timeout):
    basis_json = [_point_json(P) for P in basis]
    key = lattice_key(
        curve_id=curve_id, source="kihara_chart_basis", basis=basis_json,
        precision_bits=precision, family_spec="kihara2001_rank14",
    )
    cached = db.execute("SELECT * FROM mw_lattices WHERE lattice_key=?", (key,)).fetchone()
    if cached is not None:
        return {
            "count": int(cached["basis_count"]),
            "precision_bits": int(cached["precision_bits"]),
            "gram": json.loads(cached["gram_json"] or "[]"),
            "determinant": cached["determinant"],
            "min_eigenvalue": cached["min_eigenvalue"],
            "positive_definite_screen": bool(cached["positive_definite_screen"]),
            "cached_lattice_id": int(cached["id"]),
        }
    result = run_height_screen(E, basis, precision=precision, timeout=timeout)
    stored = store_lattice(
        db, curve_id=curve_id, source="kihara_chart_basis",
        family_spec="kihara2001_rank14", parameter=parameter, basis=basis_json,
        gram=result.get("gram") or [], precision_bits=precision,
        determinant=result.get("determinant"),
        min_eigenvalue=result.get("min_eigenvalue"),
        positive_definite_screen=bool(result.get("positive_definite_screen")),
        metadata={
            "purpose": "cached post-hit 14-section numerical height screen",
            "runtime_seconds": result.get("runtime_seconds"),
            "proof_status": "numerical_screen_only",
        },
    )
    result["cached_lattice_id"] = int(stored["id"])
    return result


def _run_one(db, cand, args, rpinfo, index, total):
    t = QQ(str(cand["t"]))
    param = str(t)
    score = float(cand.get("score", 0.0))
    curve_id = cand.get("curve_id")
    if curve_id is None:
        existing = get_curve_by_key(db, family.name(), param)
        curve_id = int(existing["id"]) if existing is not None else upsert_curve(
            db, family=family.name(), parameter=param, score=score
        )
    else:
        curve_id = int(curve_id)

    reconcile = reconcile_specialization_lower(db, curve_id)
    if reconcile.get("cleared"):
        print(f"    cleared unsupported legacy generic lower {reconcile['previous_lower']}")

    print()
    print(f"[{index}/{total}] curve #{curve_id} t={param} score={score:.6f}")
    print("    building native quartic + known section fibers...")
    started = time.monotonic()
    try:
        native_coeffs = family.quartic_search_coefficients(t)
        known_native = family.native_quartic_known_points(t)
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Kihara chart construction failed: {exc!r}")
        print("    CONSTRUCTION ERROR:", repr(exc))
        return
    known_x = {_fq(x) for x, _ in known_native}
    print(f"    native data ready in {time.monotonic()-started:.2f}s; ranking charts...")

    charts = rank_charts(
        native_coeffs, known_x, anchor_pool=args.anchor_pool, limit=args.charts
    )
    if not charts:
        print("    no usable Mobius charts")
        return
    for j, chart in enumerate(charts, 1):
        print(
            f"    chart {j}: quality={chart.quality:.1f} "
            f"coeffbits={chart.max_coeff_bits} knownbits={chart.max_known_bits} "
            f"anchors=({chart.alpha},{chart.beta},{chart.gamma})"
        )

    # native-point candidates are deduplicated across all charts and stages.
    # Value: (quartic_point_row, chart, search, stage_height, x, y)
    native_hits = {}
    native_poly = [_fq(c) for c in native_coeffs]

    for j, chart in enumerate(charts, 1):
        print(f"    [chart {j}/{len(charts)}]")
        chart_timed_out = False
        for height in args.stages:
            search, qrows, stop_chart = _search_chart_stage(
                db, curve_id=curve_id, param=param, score=score,
                chart=chart, chart_rank=j, height=height,
                args=args, rpinfo=rpinfo,
            )
            if stop_chart:
                chart_timed_out = True
                break
            for qrow in qrows:
                mapped = inverse_point(chart, qrow["x"], qrow["y"])
                if mapped is None:
                    continue
                x, y = mapped
                if y * y != evaluate(native_poly, x):
                    raise ArithmeticError("Mobius inverse failed exact native-quartic check")
                meta = json.loads(qrow["metadata_json"] or "{}")
                meta.update({
                    "native_x": str(x), "native_y": str(y),
                    "mobius_chart": chart.as_metadata(),
                })
                db.execute(
                    "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                    (json.dumps(meta, sort_keys=True), qrow["id"]),
                )
                db.commit()
                if not args.include_known_fibers and x in known_x:
                    continue
                native_hits[(x, y)] = (qrow, chart, search, height, x, y)
        if chart_timed_out:
            continue

    if not native_hits:
        print("    no new native quartic x-fibers found -> no elliptic model needed")
        update_curve(db, curve_id, status="extra_done", error=None)
        return

    print(f"    NEW NATIVE QUARTIC HIT(S): {len(native_hits)}; materializing 14-section model...")
    try:
        bundle = family.direct_search_bundle(t)
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Kihara full model after chart hit failed: {exc!r}")
        print("    FULL MODEL ERROR:", repr(exc))
        return

    E = bundle["curve"]
    basis = list(bundle["basis"])
    known_E = {_canonical_point_key(P) for P in basis if not P.is_zero()}

    # Positive-control classification for the exhaustive known-fibre mode.
    # On this quartic, (x,y)->(x,-y) maps to P->T-P rather than necessarily
    # to elliptic negation.  Classify those exact structural controls before
    # the ordinary extra-point filter so they cannot masquerade as rank growth.
    involution_control_keys = {}
    involution_translation = None
    if args.include_known_fibers:
        try:
            controls = family.native_quartic_involution_controls(bundle, t)
            involution_translation = controls[0]["translation"] if controls else None
            for rec in controls:
                Q = rec["opposite_image"]
                if not Q.is_zero():
                    involution_control_keys[_canonical_point_key(Q)] = int(rec["index"])
            if involution_translation is not None:
                if involution_translation.is_zero():
                    tdesc = "O"
                else:
                    tdesc = f"({involution_translation[0]}, {involution_translation[1]})"
                print(
                    "    positive control: exact quartic involution verified on "
                    f"{len(controls)} published fibres; P -> T-P with T={tdesc}"
                )
                log_event(
                    db, curve_id, "info",
                    "Kihara positive control verified exactly: quartic involution "
                    f"P -> T-P on {len(controls)} published fibres; T={tdesc}",
                )
        except Exception as exc:
            update_curve(db, curve_id, status="error", error=repr(exc))
            log_event(db, curve_id, "error", f"Kihara involution positive control failed: {exc!r}")
            print("    POSITIVE CONTROL ERROR:", repr(exc))
            return

    update_curve(
        db, curve_id,
        a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]),
        status="extra_searching", error=None,
    )

    mapped_candidates = []
    seen_E = set()
    for qrow, chart, search, height, x, y in native_hits.values():
        try:
            P = family.map_native_quartic_point(bundle, x, y)
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
        key = _canonical_point_key(P)
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
            meta = json.loads(qrow["metadata_json"] or "{}")
            meta.update({
                "classification": "known_quartic_involution_control",
                "published_fibre_index": involution_control_keys[key],
                "involution_translation": None if involution_translation is None or involution_translation.is_zero() else [
                    str(involution_translation[0]), str(involution_translation[1])
                ],
                "proof_status": "exact_structural_identity",
            })
            db.execute(
                "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                (json.dumps(meta, sort_keys=True), qrow["id"]),
            )
            db.commit()
            continue
        covering = store_covering(
            db, _covering_payload(curve_id, bundle, chart, height, search["id"])
        )
        update_covering(db, covering["id"], quartic_search_id=search["id"], status="mapped")
        mapped_candidates.append((qrow, covering, P))

    print(f"    mapped unique points outside known ±sections = {len(mapped_candidates)}")
    if not mapped_candidates:
        update_curve(db, curve_id, status="extra_done", error=None)
        return

    print(
        f"    [exact] certifying 14 specialized sections "
        f"(hard timeout {args.certificate_timeout}s)..."
    )
    baseline_cert = certify_specialized_sections(
        db, curve_id=curve_id, E=E, basis=basis, parameter=param,
        timeout=args.certificate_timeout,
    )
    if baseline_cert.get("independent"):
        print(f"        CERTIFIED -> rigorous specialization lower >= {baseline_cert['rigorous_lower']}")
    else:
        print(
            f"        {str(baseline_cert.get('status') or 'inconclusive').upper()} "
            "-> no rigorous generic lower written"
        )

    print(
        f"    [height] checking/caching 14-section basis at {args.precision} bits "
        f"(hard timeout {args.height_timeout}s)..."
    )
    try:
        basis_screen = _basis_height_screen(
            db, curve_id=curve_id, E=E, basis=basis, parameter=param,
            precision=args.precision, timeout=args.height_timeout,
        )
        if basis_screen.get("cached_lattice_id"):
            print(f"        lattice cache id #{basis_screen['cached_lattice_id']}")
    except HeightScreenTimeout as exc:
        print(f"    basis height screen TIMEOUT: {exc}; mapped points saved for review")
        update_curve(db, curve_id, status="extra_review", error=None)
        log_event(db, curve_id, "height_timeout", str(exc))
        return
    except (HeightScreenFailure, Exception) as exc:
        basis_screen = {"positive_definite_screen": False, "error": repr(exc)}
    if not basis_screen.get("positive_definite_screen"):
        print("    basis height screen FAILED; mapped points saved for review")
        update_curve(db, curve_id, status="extra_review", error=None)
        return

    working = list(basis)
    accepted = 0
    for qrow, covering, P in mapped_candidates:
        before = len(working)
        print(
            f"    [height] candidate against basis size {before} "
            f"(hard timeout {args.height_timeout}s)..."
        )
        try:
            screen = run_height_screen(
                E, working + [P], precision=args.precision, timeout=args.height_timeout
            )
        except HeightScreenTimeout as exc:
            screen = {
                "positive_definite_screen": False, "status": "timeout",
                "error": str(exc), "precision_bits": args.precision,
            }
            print("        TIMEOUT -> exact point saved; independence remains unclassified")
        except HeightScreenFailure as exc:
            screen = {
                "positive_definite_screen": False, "status": "error",
                "error": str(exc), "precision_bits": args.precision,
            }
        independent = bool(screen.get("positive_definite_screen"))
        if independent:
            working.append(P)
            accepted += 1
            print(f"        PASS -> screened basis size {len(working)}")
        else:
            print("        dependent/indeterminate")
        store_extra_point(
            db,
            covering_id=covering["id"], quartic_point_id=qrow["id"],
            curve_id=curve_id, x=P[0], y=P[1], exact_verified=True,
            independence_screen=independent,
            basis_count_before=before, basis_count_after=len(working),
            determinant=screen.get("determinant"),
            min_eigenvalue=screen.get("min_eigenvalue"),
            metadata={
                "precision_bits": args.precision,
                "source": "kihara_mobius_ratpoints",
                "screen_only": True,
                "error": screen.get("error"),
            },
        )

    if accepted:
        update_curve(
            db, curve_id,
            generators_json=json.dumps([[str(P[0]), str(P[1])] for P in working]),
            status="extra_candidate", error=None,
        )
        screened_lower = 14 + accepted
        log_event(
            db, curve_id, "prom",
            f"Kihara Mobius scout produced {accepted} extra independence screen(s); "
            f"screened basis size {screened_lower}",
        )
        print()
        print("    " + "*" * 60)
        print(f"    EXTRA-POINT HIT: basis 14 -> {screened_lower} (screened)")
        if screened_lower > 15:
            print("    *** SCREENED BASIS EXCEEDS PROJECT INCUMBENT 15 ***")
        print("    NOTE: numerical independence screen; certify before scoreboard update")
        print("    " + "*" * 60)
    else:
        update_curve(db, curve_id, status="extra_done", error=None)


def main():
    args = parse_args()
    db = connect(args.db)
    try:
        rpinfo = probe_version(args.ratpoints)
    except RatpointsNotFound as exc:
        raise SystemExit(str(exc))

    if args.id is not None:
        candidates = [_candidate_from_id(db, args.id)]
    else:
        candidates = []
        for row in _candidate_rows(args.input, args.limit):
            declared = row.get("family")
            if declared and declared != family.name():
                raise SystemExit(
                    f"candidate family {declared!r} does not match {family.name()!r}"
                )
            candidates.append({
                "t": _row_parameter(row),
                "score": float(row.get("score", 0.0)),
            })

    print("RANK HUNTER KIHARA MOBIUS-CHART SCOUT")
    print("=" * 72)
    print("family              =", family.name())
    print("ratpoints           =", rpinfo["executable"])
    print("ratpoints version   =", rpinfo["version"] or "unknown")
    print("candidates          =", len(candidates))
    print("charts/candidate    =", args.charts)
    print("anchor pool         =", args.anchor_pool)
    print("height stages       =", ",".join(str(x) for x in args.stages))
    print("timeout/chart-stage =", args.timeout, "s")
    print("height precision    =", args.precision, "bits after a new-x hit")
    print("height timeout      =", args.height_timeout, "s per numerical screen")
    print("certificate timeout =", args.certificate_timeout, "s for exact section baseline")
    print("known x-fibers      =", "included" if args.include_known_fibers else "skipped")

    for i, cand in enumerate(candidates, 1):
        try:
            _run_one(db, cand, args, rpinfo, i, len(candidates))
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print("    UNEXPECTED ERROR:", repr(exc))
            curve_id = cand.get("curve_id")
            if curve_id is not None:
                update_curve(db, int(curve_id), status="error", error=repr(exc))
                log_event(db, int(curve_id), "error", f"Kihara Mobius scout: {exc!r}")
        print(f"[candidate done] {i}/{len(candidates)}", flush=True)

    print()
    print("[done] Kihara Mobius-chart scout complete")


if __name__ == "__main__":
    main()
