"""Direct extra-point scout for Kihara's rank-14 family.

This is deliberately *not* a descent gate.  For each specialization we search
Kihara's native quartic with ratpoints first.  Only when rational points are
found do we materialize the full Weierstrass model, the fourteen published
sections, and Neron--Tate height screens.

A positive-definite numerical height matrix is stored as a rank-growth screen,
not silently promoted to a formal rank proof.
"""

from __future__ import annotations

import argparse
import json
import time
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
from rank42.lattice_store import store_covering, store_extra_point, update_covering
from rank42.mathutil import height_screen
from rank42.quartic_store import (
    create_or_get_search, finish_search, mark_running, store_points,
)
from rank42.ratpoints import (
    RatpointsFailure, RatpointsNotFound, RatpointsTimeout,
    normalize_polynomial, probe_version, run_ratpoints,
)


def _canonical_point_key(P):
    Q = -P
    return min((QQ(P[0]), QQ(P[1])), (QQ(Q[0]), QQ(Q[1])))


def _candidate_rows(path, limit):
    rows = []
    with Path(path).open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)
    return rows[: int(limit)]


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


def _covering_payload(curve_id, bundle, height, *, denominator_low=None,
                      denominator_high=None, extra_args=None, search_id=None):
    return {
        "schema": "rank42.covering.v1",
        "curve_id": int(curve_id),
        "quartic": {
            "coefficients": [str(x) for x in bundle["quartic_coefficients"]],
            "height": int(height),
            "denominator_low": denominator_low,
            "denominator_high": denominator_high,
            "extra_args": list(extra_args or []),
        },
        "map": family.covering_map_expressions(bundle),
        "metadata": {
            "source": "kihara2001_native_quartic",
            "historical_generic_rank_lower": 14,
            "generic_rank_claim_state": "sections_verified",
            "quartic_search_id": search_id,
        },
    }


def parse_args():
    ap = argparse.ArgumentParser(
        description="Search Kihara rank-14 quartics directly for extra rational points."
    )
    ap.add_argument("--db", default="rank42.db")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--id", type=int, help="target one stored Kihara curve id")
    src.add_argument("--input", help="Nagao candidate JSONL")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--height", type=int, default=100000)
    ap.add_argument("--timeout", type=int, default=60,
                    help="ratpoints timeout per specialization")
    ap.add_argument("--precision", type=int, default=128,
                    help="height precision, used only after a possible new mapped point")
    ap.add_argument("--certificate-timeout", type=int, default=120,
                    help="hard timeout for exact 14-section specialization certificate")
    ap.add_argument("--denominator-low", type=int)
    ap.add_argument("--denominator-high", type=int)
    ap.add_argument("--ratpoints")
    ap.add_argument("--extra-arg", action="append", default=[])
    ap.add_argument("--force", action="store_true", help="rerun completed quartic searches")
    return ap.parse_args()


def _run_one(db, cand, args, rpinfo, index, total):
    t = QQ(str(cand["t"]))
    param = str(t)
    score = float(cand.get("score", 0.0))
    curve_id = cand.get("curve_id")
    if curve_id is None:
        existing = get_curve_by_key(db, family.name(), param)
        if existing is not None:
            curve_id = int(existing["id"])
        else:
            curve_id = upsert_curve(
                db, family=family.name(), parameter=param, score=score
            )
    else:
        curve_id = int(curve_id)

    reconcile = reconcile_specialization_lower(db, curve_id)
    if reconcile.get("cleared"):
        print(f"    cleared unsupported legacy generic lower {reconcile['previous_lower']}")

    print()
    print(f"[{index}/{total}] curve #{curve_id} t={param} score={score:.6f}")
    print("    constructing native Kihara quartic...")
    started = time.monotonic()
    try:
        coeffs = family.quartic_search_coefficients(t)
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Kihara quartic construction failed: {exc!r}")
        print("    QUARTIC ERROR:", repr(exc))
        return
    build_time = time.monotonic() - started

    norm = normalize_polynomial(coeffs)
    search = create_or_get_search(
        db,
        curve_id=curve_id,
        family=family.name(),
        parameter=param,
        hole_label="kihara-native",
        coefficients=norm.rational_coefficients,
        integer_coefficients=norm.integer_coefficients,
        y_scale=norm.y_scale,
        degree=norm.degree,
        height_bound=args.height,
        denominator_low=args.denominator_low,
        denominator_high=args.denominator_high,
        extra_args=args.extra_arg,
        metadata={
            "source": "kihara2001_native_quartic",
            "score": score,
            "construction_seconds": build_time,
        },
    )

    if search["status"] == "done" and not args.force:
        print(
            f"    reusing quartic search #{search['id']} "
            f"({search['point_count'] or 0} point(s))"
        )
    else:
        mark_running(db, search["id"], executable=rpinfo["executable"])
        print(
            f"    ratpoints H={args.height} timeout={args.timeout}s "
            f"(quartic build {build_time:.2f}s)..."
        )
        rp_started = time.monotonic()
        try:
            result = run_ratpoints(
                norm.rational_coefficients,
                args.height,
                executable=rpinfo["executable"],
                timeout=args.timeout,
                denominator_low=args.denominator_low,
                denominator_high=args.denominator_high,
                extra_args=args.extra_arg,
            )
        except RatpointsTimeout as exc:
            runtime = time.monotonic() - rp_started
            finish_search(db, search["id"], status="timeout", runtime=runtime, error=str(exc))
            log_event(db, curve_id, "warn", f"Kihara ratpoints timeout H={args.height}")
            print("    RATPOINTS TIMEOUT")
            return
        except RatpointsFailure as exc:
            runtime = time.monotonic() - rp_started
            finish_search(db, search["id"], status="error", runtime=runtime, error=str(exc))
            log_event(db, curve_id, "error", f"Kihara ratpoints failed: {exc}")
            print("    RATPOINTS ERROR")
            print("   ", exc)
            return
        store_points(db, search["id"], result["points"])
        finish_search(
            db, search["id"], status="done", runtime=result["runtime"],
            point_count=len(result["points"]), error=None,
        )
        print(f"    ratpoints found {len(result['points'])} finite point(s) in {result['runtime']:.2f}s")

    qrows = db.execute(
        "SELECT * FROM quartic_points WHERE search_id=? ORDER BY id",
        (search["id"],),
    ).fetchall()
    if not qrows:
        print("    no quartic points -> next candidate")
        return

    # Pay the full-model cost only after the cheap quartic search produced data.
    print(f"    materializing 14-section model for {len(qrows)} quartic point(s)...")
    try:
        bundle = family.direct_search_bundle(t)
    except Exception as exc:
        update_curve(db, curve_id, status="error", error=repr(exc))
        log_event(db, curve_id, "error", f"Kihara full model failed after quartic hit: {exc!r}")
        print("    FULL MODEL ERROR:", repr(exc))
        return

    E = bundle["curve"]
    basis = list(bundle["basis"])
    update_curve(
        db,
        curve_id,
        a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]),
        status="extra_searching",
        error=None,
    )

    covering_data = _covering_payload(
        curve_id, bundle, args.height,
        denominator_low=args.denominator_low,
        denominator_high=args.denominator_high,
        extra_args=args.extra_arg,
        search_id=search["id"],
    )
    covering = store_covering(db, covering_data)
    update_covering(db, covering["id"], quartic_search_id=search["id"], status="searched")

    known = {_canonical_point_key(P) for P in basis if not P.is_zero()}
    mapped = []
    seen = set()
    for qrow in qrows:
        try:
            P = family.map_native_quartic_point(bundle, qrow["x"], qrow["y"])
        except Exception as exc:
            meta = json.loads(qrow["metadata_json"] or "{}")
            meta["map_error"] = repr(exc)
            db.execute(
                "UPDATE quartic_points SET metadata_json=? WHERE id=?",
                (json.dumps(meta, sort_keys=True), qrow["id"]),
            )
            db.commit()
            continue
        if P.is_zero():
            continue
        db.execute(
            "UPDATE quartic_points SET mapped_point_json=? WHERE id=?",
            (json.dumps([str(P[0]), str(P[1])]), qrow["id"]),
        )
        db.commit()
        key = _canonical_point_key(P)
        if key in seen:
            continue
        seen.add(key)
        mapped.append((qrow, P, key))

    candidates = [(qrow, P) for qrow, P, key in mapped if key not in known]
    print(f"    mapped unique nonzero = {len(mapped)}; outside known ±sections = {len(candidates)}")
    if not candidates:
        update_covering(db, covering["id"], status="mapped")
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

    print(f"    [height] screening 14-section basis at {args.precision} bits...")
    try:
        basis_screen = height_screen(E, basis, precision=args.precision)
    except Exception as exc:
        basis_screen = {"positive_definite_screen": False, "error": repr(exc)}
    if not basis_screen.get("positive_definite_screen"):
        print("    basis height screen FAILED; mapped points persisted but not numerically ranked")
        update_covering(db, covering["id"], status="mapped")
        update_curve(db, curve_id, status="extra_review", error=None)
        return

    working = list(basis)
    accepted = 0
    for qrow, P in candidates:
        before = len(working)
        print(f"    [height] candidate against {before} point(s)...")
        try:
            screen = height_screen(E, working + [P], precision=args.precision)
        except Exception as exc:
            screen = {"positive_definite_screen": False, "error": repr(exc)}
        independent = bool(screen.get("positive_definite_screen"))
        if independent:
            working.append(P)
            accepted += 1
            print(f"        PASS -> screened basis size {len(working)}")
        else:
            print("        dependent/indeterminate at this screen")
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
                "source": "kihara_direct_ratpoints",
                "screen_only": True,
                "error": screen.get("error"),
            },
        )

    update_covering(db, covering["id"], status="mapped")
    if accepted:
        combined = [[str(P[0]), str(P[1])] for P in working]
        update_curve(
            db, curve_id, generators_json=json.dumps(combined),
            status="extra_candidate", error=None,
        )
        screened_lower = 14 + accepted
        log_event(
            db, curve_id, "prom",
            f"Kihara direct ratpoints produced {accepted} extra independence screen(s); "
            f"screened basis size {screened_lower}",
        )
        print()
        print("    " + "*" * 58)
        print(f"    EXTRA-POINT HIT: {accepted} new screen(s); basis 14 -> {screened_lower}")
        if screened_lower > 15:
            print("    *** SCREENED BASIS EXCEEDS PROJECT INCUMBENT 15 ***")
        print("    NOTE: numerical height screen; run targeted certification before scoreboard update")
        print("    " + "*" * 58)
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
        raw = _candidate_rows(args.input, args.limit)
        candidates = []
        for row in raw:
            declared = row.get("family")
            if declared and declared != family.name():
                raise SystemExit(
                    f"candidate family {declared!r} does not match {family.name()!r}"
                )
            candidates.append({
                "t": str(QQ(row["a"]) / QQ(row["b"])),
                "score": float(row["score"]),
            })

    print("RANK HUNTER KIHARA DIRECT EXTRA-POINT SCOUT")
    print("=" * 72)
    print("family              =", family.name())
    print("ratpoints           =", rpinfo["executable"])
    print("ratpoints version   =", rpinfo["version"] or "unknown")
    print("candidates          =", len(candidates))
    print("height              =", args.height)
    print("timeout/candidate   =", args.timeout, "s")
    print("height precision    =", args.precision, "bits (only after a possible hit)")
    print("certificate timeout =", args.certificate_timeout, "s for exact section baseline")

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
                log_event(db, int(curve_id), "error", f"Kihara extra scout: {exc!r}")

    print()
    print("[done] direct Kihara quartic scout complete")


if __name__ == "__main__":
    main()
