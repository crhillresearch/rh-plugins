#!/usr/bin/env python3
"""Subgroup-aware Family/Target search for Elkies X1092 Published MW17.

Scientific policy:
* the generic MW17 theorem is not an automatic specialization rank claim;
* S1..S17 are instantiated exactly on every specialization before use;
* specialization lower bounds rise only through Rank Hunter's exact
  independence-certificate path;
* ratpoints hits remain candidate extras until exact independence is certified;
* this RELEASE runner does not reintroduce excluded quadratic rank-jump tooling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _find_project_root():
    starts = (Path.cwd().resolve(), Path(__file__).resolve().parent)
    seen = set()
    for start in starts:
        for candidate in (start, *start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / "rank42").is_dir():
                return candidate
    return Path.cwd().resolve()


PROJECT_ROOT = _find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.all import QQ

from rank42.db import (
    connect,
    get_curve,
    get_curve_by_key,
    log_event,
    proven_lower,
    upsert_curve,
    update_curve,
)
from rank42.exact_lb import (
    ExactCertificateFailure,
    ExactCertificateTimeout,
    run_exact_certificate,
)
from rank42.family_loader import load_family
from rank42.points import upsert_point
from rank42.rank_evidence import apply_reduced_rank_state, record_rank_evidence
from rank42.ratpoints import (
    RatpointsFailure,
    RatpointsNotFound,
    RatpointsTimeout,
    probe_version,
    run_ratpoints,
)

PLUGIN_ID = "elkies_x1092_rank17"
PLUGIN_VERSION = "1.3.0"
FAMILY_NAME = "Elkies X1092 published rank-17 fibration"
EXPECTED_FAMILY_NAME = "Elkies X1092 published rank-17 fibration"
BASELINE_RANK = 17


def parse_stages(text):
    values = sorted(
        set(int(value.strip()) for value in str(text).split(",") if value.strip())
    )
    if not values or values[0] <= 0:
        raise argparse.ArgumentTypeError("positive comma-separated stages required")
    return values


def parse_args():
    ap = argparse.ArgumentParser(
        description="Elkies X1092 MW17 subgroup-aware Family/Target search"
    )
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--curve-id", type=int)
    ap.add_argument("--db", default="rank42.db")
    ap.add_argument("--family", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--stages", type=parse_stages, default=parse_stages("1000,10000"))
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--ratpoints")
    ap.add_argument("--baseline-certificate", action="store_true")
    ap.add_argument("--baseline-timeout", type=int, default=180)
    ap.add_argument("--exact-candidates", type=int, default=8)
    ap.add_argument("--certificate-timeout", type=int, default=180)
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def point_key(point):
    negative = -point
    return min(
        (QQ(point[0]), QQ(point[1])),
        (QQ(negative[0]), QQ(negative[1])),
    )


def parameter_of(row):
    for key in ("t", "parameter", "r", "s"):
        if row.get(key) is not None:
            return QQ(str(row[key]))
    return QQ(str(row["a"])) / QQ(str(row["b"]))


def load_rows(path, limit):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
            if len(rows) >= int(limit):
                break
    return rows


def cert_points(curve, points, timeout):
    return run_exact_certificate(
        curve.a_invariants(),
        [[str(point[0]), str(point[1])] for point in points],
        timeout=int(timeout),
    )


def _basis_payload(points):
    return [[str(point[0]), str(point[1])] for point in points]


def _basis_fingerprint(points):
    payload = json.dumps(
        _basis_payload(points),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_subgroup_evidence(db, curve_id, curve, points, result, *, source):
    certificate = result.get("certificate") or {}
    lower = len(points)
    record_rank_evidence(
        db,
        curve_id=int(curve_id),
        model=[str(a) for a in curve.a_invariants()],
        data={
            "engine": "rank42.exact_lb",
            "evidence_type": "certified_subgroup",
            "status": "completed",
            "rigorous": True,
            "rigorous_lower": lower,
            "rigorous_upper": None,
            "exact_rank": None,
            "assumptions": [],
            "points_found": _basis_payload(points),
            "minimal_model_a_invariants": (
                result.get("minimal_model") or {}
            ).get("a_invariants"),
            "options": {
                "plugin_id": PLUGIN_ID,
                "plugin_version": PLUGIN_VERSION,
                "source": str(source),
                "basis_size": lower,
                "basis_sha256": _basis_fingerprint(points),
                "certificate_method": certificate.get("method"),
            },
            "elapsed_seconds": result.get("runtime_seconds"),
            "stdout_summary": json.dumps(
                {"certificate": certificate},
                sort_keys=True,
            ),
        },
    )
    return apply_reduced_rank_state(db, int(curve_id))


def _section_metadata(family, parameter, count):
    provider = getattr(family, "generic_section_metadata", None)
    if not callable(provider):
        return [{} for _ in range(count)]
    records = list(provider(parameter) or [])
    if len(records) != count:
        return [{} for _ in range(count)]
    return records


def save_baseline_points(
    db,
    curve_id,
    points,
    metadata,
    *,
    rigorous=False,
    certificate=None,
):
    for index, point in enumerate(points, 1):
        section = dict(metadata[index - 1] or {})
        section.setdefault("basis_label", f"S{index}")
        section["certificate"] = certificate if rigorous else None
        upsert_point(
            db,
            curve_id=curve_id,
            x=point[0],
            y=point[1],
            source="elkies_x1092_published_section",
            role="rigorous_witness" if rigorous else "generic_section",
            exact_verified=True,
            independence_status="rigorous_independent" if rigorous else "unknown",
            rigorous_independent=rigorous,
            search_ref="elkies-x1092:published-mw17",
            plugin_id=PLUGIN_ID,
            metadata=section,
        )


def certify_baseline(db, curve_id, curve, baseline, metadata, timeout):
    try:
        result = cert_points(curve, baseline, timeout)
    except (ExactCertificateTimeout, ExactCertificateFailure) as exc:
        log_event(
            db,
            curve_id,
            "warn",
            f"X1092 S1..S17 baseline certificate inconclusive: {exc}",
        )
        print(f"    baseline exact certificate INCONCLUSIVE: {exc}", flush=True)
        return False, None

    if result.get("independent"):
        current = get_curve(db, curve_id)
        prior_lower = int(current["descent_lower"] or 0)
        fields = {
            "generic_lower": max(BASELINE_RANK, int(current["generic_lower"] or 0)),
            "status": "proven_lower",
            "error": None,
        }
        if prior_lower <= BASELINE_RANK:
            fields["descent_lower"] = BASELINE_RANK
            fields["generators_json"] = json.dumps(_basis_payload(baseline))
        update_curve(db, curve_id, **fields)
        record_subgroup_evidence(
            db,
            curve_id,
            curve,
            baseline,
            result,
            source="x1092_published_mw17_baseline",
        )
        save_baseline_points(
            db,
            curve_id,
            baseline,
            metadata,
            rigorous=True,
            certificate=result.get("certificate"),
        )
        log_event(
            db,
            curve_id,
            "info",
            "exact specialized X1092 MW17 baseline certified rank >=17",
        )
        print(
            f"    baseline CERTIFIED: rank >=17 "
            f"({result.get('runtime_seconds', 0):.2f}s)",
            flush=True,
        )
        return True, result

    if result.get("status") == "dependent":
        update_curve(
            db,
            curve_id,
            status="baseline_dependent",
            error="published X1092 sections specialize dependently at this parameter",
        )
        log_event(
            db,
            curve_id,
            "warn",
            "published X1092 S1..S17 specialize dependently",
        )
        print("    baseline exactly DEPENDENT at this specialization", flush=True)
        return False, result

    print("    baseline exact certificate inconclusive", flush=True)
    return False, result


def search_ratpoints(curve, stages, executable, timeout):
    short_curve = curve.short_weierstrass_model()
    to_original = short_curve.isomorphism_to(curve)
    a_invariants = list(short_curve.a_invariants())
    if any(a_invariants[index] != 0 for index in (0, 1, 2)):
        raise RuntimeError(
            "short Weierstrass conversion did not produce [0,0,0,A,B]"
        )

    a4, a6 = a_invariants[3], a_invariants[4]
    polynomial = [a6, a4, QQ(0), QQ(1)]
    found = {}

    for height in stages:
        try:
            result = run_ratpoints(
                polynomial,
                height,
                executable=executable,
                timeout=timeout,
            )
        except RatpointsTimeout:
            print(f"    [ratpoints] H={height} TIMEOUT", flush=True)
            continue
        except RatpointsFailure as exc:
            print(f"    [ratpoints] H={height} ERROR {exc}", flush=True)
            continue

        added = 0
        for raw in result["points"]:
            try:
                point = to_original(
                    short_curve(QQ(str(raw.x)), QQ(str(raw.y)))
                )
            except Exception:
                continue
            if point.is_zero():
                continue
            key = point_key(point)
            if key in found:
                continue
            found[key] = point
            added += 1

        print(
            f"    [ratpoints] H={height} raw={len(result['points'])} "
            f"new_exact={added} total={len(found)} "
            f"runtime={result['runtime']:.2f}s",
            flush=True,
        )

    return list(found.values())


def _stored_rigorous_basis(db, curve_id, curve, fallback):
    row = get_curve(db, curve_id)
    lower = int(proven_lower(row))
    if lower <= BASELINE_RANK:
        return list(fallback)

    try:
        stored = json.loads(row["generators_json"] or "[]")
        descent_lower = int(row["descent_lower"] or 0)
        if len(stored) >= descent_lower > BASELINE_RANK:
            return [
                curve(QQ(str(x)), QQ(str(y)))
                for x, y in stored[:descent_lower]
            ]
    except Exception:
        pass
    return list(fallback)


def process_one(
    db,
    family,
    parameter,
    score,
    args,
    ratpoints_executable,
    *,
    existing_curve_id=None,
):
    parameter_text = str(parameter)
    curve = family.curve(parameter)
    if curve is None:
        print("    singular/undefined specialization", flush=True)
        return None

    baseline = list(family.generic_section_points(parameter))
    if len(baseline) != BASELINE_RANK:
        raise RuntimeError(
            f"expected {BASELINE_RANK} specialized X1092 sections, "
            f"got {len(baseline)}"
        )
    metadata = _section_metadata(family, parameter, len(baseline))

    curve_id = existing_curve_id or upsert_curve(
        db,
        family=FAMILY_NAME,
        parameter=parameter_text,
        score=score,
    )
    update_curve(
        db,
        curve_id,
        a_invariants_json=json.dumps([str(a) for a in curve.a_invariants()]),
        status="search_running",
        error=None,
    )
    save_baseline_points(db, curve_id, baseline, metadata)

    baseline_ok = int(proven_lower(get_curve(db, curve_id))) >= BASELINE_RANK
    if args.baseline_certificate and (args.force or not baseline_ok):
        baseline_ok, _ = certify_baseline(
            db,
            curve_id,
            curve,
            baseline,
            metadata,
            args.baseline_timeout,
        )
    elif baseline_ok:
        print(
            f"    stored rigorous baseline >= "
            f"{proven_lower(get_curve(db, curve_id))}",
            flush=True,
        )
    else:
        print(
            "    S1..S17 stored exact-on-curve but not independently certified",
            flush=True,
        )

    found = search_ratpoints(
        curve,
        args.stages,
        ratpoints_executable,
        args.timeout,
    )

    baseline_keys = {point_key(point) for point in baseline}
    candidate_points = []
    for point in found:
        if point_key(point) in baseline_keys:
            continue
        candidate_points.append(point)
        upsert_point(
            db,
            curve_id=curve_id,
            x=point[0],
            y=point[1],
            source="elkies_x1092_ratpoints",
            role="candidate_extra",
            exact_verified=True,
            independence_status="unknown",
            search_ref="elkies-x1092:ratpoints",
            plugin_id=PLUGIN_ID,
        )

    print(
        f"    exact hits outside literal S1..S17 list = {len(candidate_points)}",
        flush=True,
    )

    rigorous_basis = _stored_rigorous_basis(db, curve_id, curve, baseline)
    known_keys = {point_key(point) for point in rigorous_basis}
    accepted = []
    exact_attempts = 0

    for point in candidate_points:
        if exact_attempts >= max(0, int(args.exact_candidates)):
            break
        if point_key(point) in known_keys:
            continue

        exact_attempts += 1
        trial = rigorous_basis + [point]
        try:
            result = cert_points(curve, trial, args.certificate_timeout)
        except (ExactCertificateTimeout, ExactCertificateFailure) as exc:
            print(
                f"    [exact] candidate {exact_attempts}: inconclusive {exc}",
                flush=True,
            )
            continue

        status = str(result.get("status") or "unknown")
        print(f"    [exact] candidate {exact_attempts}: {status}", flush=True)

        if result.get("independent"):
            rigorous_basis = trial
            accepted.append(point)
            known_keys.add(point_key(point))
            lower = len(rigorous_basis)
            update_curve(
                db,
                curve_id,
                generic_lower=max(
                    BASELINE_RANK,
                    int(get_curve(db, curve_id)["generic_lower"] or 0),
                ),
                descent_lower=lower,
                generators_json=json.dumps(_basis_payload(rigorous_basis)),
                status="proven_lower",
                error=None,
            )
            record_subgroup_evidence(
                db,
                curve_id,
                curve,
                rigorous_basis,
                result,
                source=f"x1092_ratpoints_extra_rank_{lower}",
            )
            upsert_point(
                db,
                curve_id=curve_id,
                x=point[0],
                y=point[1],
                source="elkies_x1092_ratpoints",
                role="rigorous_witness",
                exact_verified=True,
                independence_status="rigorous_independent",
                rigorous_independent=True,
                search_ref="elkies-x1092:exact-extra",
                plugin_id=PLUGIN_ID,
                metadata={"certificate": result.get("certificate")},
            )
            log_event(
                db,
                curve_id,
                "best",
                f"X1092 exact search improves rigorous lower bound to {lower}",
            )
            print(
                f"    >>> RIGOROUS LOWER BOUND NOW >= {lower}",
                flush=True,
            )
        elif status == "dependent":
            upsert_point(
                db,
                curve_id=curve_id,
                x=point[0],
                y=point[1],
                source="elkies_x1092_ratpoints",
                role="candidate_extra",
                exact_verified=True,
                independence_status="dependent",
                search_ref="elkies-x1092:exact-dependent",
                plugin_id=PLUGIN_ID,
                metadata={"certificate": result.get("certificate")},
            )

    row = get_curve(db, curve_id)
    if int(proven_lower(row)) >= BASELINE_RANK and row["status"] == "search_running":
        update_curve(db, curve_id, status="proven_lower")
    elif row["status"] == "search_running":
        update_curve(db, curve_id, status="screened")

    rigorous_lower = int(proven_lower(get_curve(db, curve_id)))
    return {
        "curve_id": curve_id,
        "parameter": parameter_text,
        "rigorous_lower": rigorous_lower,
        "ratpoints_exact": len(found),
        "candidate_extras": len(candidate_points),
        "exact_attempts": exact_attempts,
        "accepted_extras": len(accepted),
    }


def main():
    args = parse_args()
    db = connect(args.db)
    family = load_family(args.family, need_sections=True)
    if family.name() != EXPECTED_FAMILY_NAME:
        raise SystemExit(f"unexpected family {family.name()!r}")

    try:
        ratpoints = probe_version(args.ratpoints)
    except RatpointsNotFound as exc:
        raise SystemExit(str(exc))
    ratpoints_executable = ratpoints["executable"]

    print("RANK HUNTER · ELKIES X1092 · PUBLISHED MW17", flush=True)
    print("=" * 68, flush=True)
    print(f"[db] {args.db}", flush=True)
    print(f"[ratpoints] {ratpoints_executable}", flush=True)
    print("[baseline] exact published S1..S17 specialization", flush=True)
    print(
        "[proof policy] specialization rank rises only through "
        "exact independence certificates",
        flush=True,
    )

    if args.curve_id is not None:
        row = get_curve(db, args.curve_id)
        if row is None:
            raise SystemExit(f"curve #{args.curve_id} not found")
        if str(row["family"]) != FAMILY_NAME:
            raise SystemExit(
                f"curve #{args.curve_id} belongs to {row['family']!r}, "
                f"not {FAMILY_NAME!r}"
            )
        parameter = QQ(str(row["parameter"]))
        result = process_one(
            db,
            family,
            parameter,
            float(row["score"] or 0.0),
            args,
            ratpoints_executable,
            existing_curve_id=int(row["id"]),
        )
        print(
            "RANK42_ELKIES_X1092_SEARCH_RESULT="
            + json.dumps(result or {}, sort_keys=True),
            flush=True,
        )
        return

    rows = load_rows(args.input, args.limit)
    print(f"[queue] {len(rows)} candidates (input order preserved)", flush=True)
    completed = []

    for index, record in enumerate(rows, 1):
        parameter = parameter_of(record)
        score = float(record.get("score") or 0.0)
        print(
            f"\n[{index}/{len(rows)}] t={parameter} score={score:.6f}",
            flush=True,
        )
        existing = get_curve_by_key(db, FAMILY_NAME, str(parameter))
        if (
            existing is not None
            and not args.force
            and str(existing["status"]) in {"proven_lower", "screened"}
        ):
            print(
                f"    existing curve #{existing['id']} "
                f"status={existing['status']}; preserving evidence "
                "and rerunning requested stages",
                flush=True,
            )

        try:
            result = process_one(
                db,
                family,
                parameter,
                score,
                args,
                ratpoints_executable,
                existing_curve_id=(
                    int(existing["id"]) if existing is not None else None
                ),
            )
            if result:
                completed.append(result)
                print(
                    "    result: " + json.dumps(result, sort_keys=True),
                    flush=True,
                )
        except Exception as exc:
            if existing is not None:
                update_curve(
                    db,
                    int(existing["id"]),
                    status="error",
                    error=repr(exc),
                )
            print(f"    ERROR: {exc!r}", flush=True)

        print(f"[candidate done] {index}/{len(rows)}", flush=True)

    summary = {
        "status": "ELKIES X1092 MW17 SEARCH COMPLETE",
        "candidates_planned": len(rows),
        "candidates_completed": len(completed),
        "best_rigorous_lower": max(
            [0, *[int(item.get("rigorous_lower") or 0) for item in completed]]
        ),
        "mapped_extra_points": sum(
            int(item.get("candidate_extras") or 0) for item in completed
        ),
        "rigorous_hits": sum(
            int(item.get("accepted_extras") or 0) for item in completed
        ),
    }
    print(
        "RANK42_ELKIES_X1092_SEARCH_RESULT="
        + json.dumps(summary, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    main()
