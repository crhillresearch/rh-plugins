#!/usr/bin/env python3
"""Subgroup-aware search runner for Elkies's verified first rank-18 cover.

Scientific policy:
* generic rank >=18 is theorem/reconstruction metadata, not an automatic specialization claim;
* all 18 specialized sections are exact-on-curve before use;
* specialization lower bounds rise only through Rank Hunter's exact independence certificate;
* ratpoints hits are candidates until exact independence is certified.
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

from rank42.db import connect, get_curve, get_curve_by_key, log_event, proven_lower, upsert_curve, update_curve
from rank42.exact_lb import ExactCertificateFailure, ExactCertificateTimeout, run_exact_certificate
from rank42.family_loader import load_family
from rank42.points import upsert_point
from rank42.rank_evidence import apply_reduced_rank_state, record_rank_evidence
from rank42.ratpoints import RatpointsFailure, RatpointsNotFound, RatpointsTimeout, probe_version, run_ratpoints

PLUGIN_ID = "elkies_rank18_2026"
PLUGIN_VERSION = "0.1.1"
FAMILY_NAME = "Elkies 2026 first rank-18 quadratic cover over Q(r)"
EXPECTED_FAMILY_NAME = "Elkies 2026 rank-18 first quadratic cover"
BASELINE_RANK = 18


def parse_stages(text):
    vals = sorted(set(int(x.strip()) for x in str(text).split(",") if x.strip()))
    if not vals or vals[0] <= 0:
        raise argparse.ArgumentTypeError("positive comma-separated stages required")
    return vals


def parse_args():
    ap = argparse.ArgumentParser(description="Elkies rank-18 first-cover subgroup-aware search")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input")
    src.add_argument("--curve-id", type=int)
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


def point_key(P):
    Q = -P
    return min((QQ(P[0]), QQ(P[1])), (QQ(Q[0]), QQ(Q[1])))


def parameter_of(row):
    if row.get("r") is not None:
        return QQ(str(row["r"]))
    if row.get("parameter") is not None:
        return QQ(str(row["parameter"]))
    if row.get("s") is not None:
        return QQ(str(row["s"]))
    if row.get("t") is not None:
        return QQ(str(row["t"]))
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


def cert_points(E, points, timeout):
    return run_exact_certificate(
        E.a_invariants(),
        [[str(P[0]), str(P[1])] for P in points],
        timeout=int(timeout),
    )


def _basis_payload(points):
    return [[str(P[0]), str(P[1])] for P in points]


def _basis_fingerprint(points):
    payload = json.dumps(_basis_payload(points), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def record_subgroup_evidence(db, curve_id, E, points, cert, *, source):
    lower = len(points)
    certificate = cert.get("certificate") or {}
    record_rank_evidence(
        db,
        curve_id=int(curve_id),
        model=[str(a) for a in E.a_invariants()],
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
            "minimal_model_a_invariants": (cert.get("minimal_model") or {}).get("a_invariants"),
            "options": {
                "plugin_id": PLUGIN_ID,
                "plugin_version": PLUGIN_VERSION,
                "source": str(source),
                "basis_size": lower,
                "basis_sha256": _basis_fingerprint(points),
                "certificate_method": certificate.get("method"),
            },
            "elapsed_seconds": cert.get("runtime_seconds"),
            "stdout_summary": json.dumps({"certificate": certificate}, sort_keys=True),
        },
    )
    return apply_reduced_rank_state(db, int(curve_id))


def save_baseline_points(db, curve_id, points, rigorous=False, certificate=None):
    for idx, P in enumerate(points, 1):
        upsert_point(
            db,
            curve_id=curve_id,
            x=P[0], y=P[1],
            source="elkies_rank18_cover_section",
            role="rigorous_witness" if rigorous else "generic_section",
            exact_verified=True,
            independence_status="rigorous_independent" if rigorous else "unknown",
            rigorous_independent=rigorous,
            search_ref="elkies2026:rank18-first-cover",
            plugin_id=PLUGIN_ID,
            metadata={
                "section_label": f"P{idx:02d}",
                "recovered_anti_invariant_section": idx == 18,
                "certificate": certificate if rigorous else None,
            },
        )


def certify_baseline(db, curve_id, E, baseline, timeout):
    try:
        cert = cert_points(E, baseline, timeout)
    except (ExactCertificateTimeout, ExactCertificateFailure) as exc:
        log_event(db, curve_id, "warn", f"Elkies 18-section baseline certificate inconclusive: {exc}")
        print(f"    baseline exact certificate INCONCLUSIVE: {exc}", flush=True)
        return False, None
    if cert.get("independent"):
        current = get_curve(db, curve_id)
        prior_descent = int(current["descent_lower"] or 0)
        fields = {
            "generic_lower": max(BASELINE_RANK, int(current["generic_lower"] or 0)),
            "status": "proven_lower",
            "error": None,
        }
        if prior_descent <= BASELINE_RANK:
            fields["descent_lower"] = BASELINE_RANK
            fields["generators_json"] = json.dumps(_basis_payload(baseline))
        update_curve(db, curve_id, **fields)
        record_subgroup_evidence(db, curve_id, E, baseline, cert, source="rank18_cover_baseline")
        save_baseline_points(db, curve_id, baseline, rigorous=True, certificate=cert.get("certificate"))
        log_event(db, curve_id, "info", "exact specialized Elkies rank-18 baseline certified rank >=18")
        print(f"    baseline CERTIFIED: rank >=18 ({cert.get('runtime_seconds',0):.2f}s)", flush=True)
        return True, cert
    if cert.get("status") == "dependent":
        update_curve(db, curve_id, status="baseline_dependent", error="18 cover sections specialize dependently at this parameter")
        log_event(db, curve_id, "warn", "Elkies 18 cover sections specialize dependently")
        print("    baseline exactly DEPENDENT at this specialization", flush=True)
        return False, cert
    print("    baseline exact certificate inconclusive", flush=True)
    return False, cert


def search_ratpoints(E, stages, executable, timeout):
    Es = E.short_weierstrass_model()
    iso = Es.isomorphism_to(E)
    ainvs = list(Es.a_invariants())
    if any(ainvs[i] != 0 for i in (0, 1, 2)):
        raise RuntimeError("short Weierstrass conversion did not produce [0,0,0,A,B]")
    A, B = ainvs[3], ainvs[4]
    poly = [B, A, QQ(0), QQ(1)]
    found = {}
    for H in stages:
        try:
            res = run_ratpoints(poly, H, executable=executable, timeout=timeout)
        except RatpointsTimeout:
            print(f"    [ratpoints] H={H} TIMEOUT", flush=True)
            continue
        except RatpointsFailure as exc:
            print(f"    [ratpoints] H={H} ERROR {exc}", flush=True)
            continue
        added = 0
        for q in res["points"]:
            try:
                P = iso(Es(QQ(str(q.x)), QQ(str(q.y))))
            except Exception:
                continue
            if P.is_zero():
                continue
            key = point_key(P)
            if key in found:
                continue
            found[key] = P
            added += 1
        print(f"    [ratpoints] H={H} raw={len(res['points'])} new_exact={added} total={len(found)} runtime={res['runtime']:.2f}s", flush=True)
    return list(found.values())


def process_one(db, family, r, score, args, rp_exe, existing_curve_id=None):
    param = str(r)
    E = family.curve(r)
    if E is None:
        print("    singular/undefined specialization", flush=True)
        return None
    baseline = family.generic_section_points(r)
    if len(baseline) != BASELINE_RANK:
        raise RuntimeError(f"expected {BASELINE_RANK} specialized cover sections, got {len(baseline)}")

    curve_id = existing_curve_id or upsert_curve(db, family=FAMILY_NAME, parameter=param, score=score)
    update_curve(db, curve_id, a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]), status="search_running", error=None)
    save_baseline_points(db, curve_id, baseline, rigorous=False)

    baseline_ok = int(proven_lower(get_curve(db, curve_id))) >= BASELINE_RANK
    if args.baseline_certificate and (args.force or not baseline_ok):
        baseline_ok, _ = certify_baseline(db, curve_id, E, baseline, args.baseline_timeout)
    elif baseline_ok:
        print(f"    stored rigorous baseline >= {proven_lower(get_curve(db, curve_id))}", flush=True)
    else:
        print("    18 specialized cover sections stored exact-on-curve but not independently certified", flush=True)

    found = search_ratpoints(E, args.stages, rp_exe, args.timeout)
    baseline_keys = {point_key(P) for P in baseline}
    candidate_points = []
    for P in found:
        if point_key(P) in baseline_keys:
            continue
        candidate_points.append(P)
        upsert_point(
            db, curve_id=curve_id, x=P[0], y=P[1],
            source="elkies_rank18_ratpoints", role="candidate_extra",
            exact_verified=True, independence_status="unknown",
            search_ref="elkies2026:rank18-ratpoints", plugin_id=PLUGIN_ID,
        )
    print(f"    exact hits outside literal P01..P18 list = {len(candidate_points)}", flush=True)

    rigorous_basis = list(baseline)
    accepted = []
    exact_attempts = 0
    if int(proven_lower(get_curve(db, curve_id))) > BASELINE_RANK:
        row = get_curve(db, curve_id)
        try:
            stored = json.loads(row["generators_json"] or "[]")
            lower = int(row["descent_lower"] or 0)
            if len(stored) >= lower > BASELINE_RANK:
                rigorous_basis = [E(QQ(str(x)), QQ(str(y))) for x, y in stored[:lower]]
        except Exception:
            rigorous_basis = list(baseline)

    known_keys = {point_key(P) for P in rigorous_basis}
    for P in candidate_points:
        if exact_attempts >= max(0, int(args.exact_candidates)):
            break
        if point_key(P) in known_keys:
            continue
        exact_attempts += 1
        trial = rigorous_basis + [P]
        try:
            cert = cert_points(E, trial, args.certificate_timeout)
        except (ExactCertificateTimeout, ExactCertificateFailure) as exc:
            print(f"    [exact] candidate {exact_attempts}: inconclusive {exc}", flush=True)
            continue
        status = str(cert.get("status") or "unknown")
        print(f"    [exact] candidate {exact_attempts}: {status}", flush=True)
        if cert.get("independent"):
            rigorous_basis = trial
            accepted.append(P)
            known_keys.add(point_key(P))
            lower = len(rigorous_basis)
            update_curve(
                db, curve_id,
                generic_lower=max(BASELINE_RANK, int(get_curve(db, curve_id)["generic_lower"] or 0)),
                descent_lower=lower,
                generators_json=json.dumps(_basis_payload(rigorous_basis)),
                status="proven_lower", error=None,
            )
            record_subgroup_evidence(db, curve_id, E, rigorous_basis, cert, source=f"rank18_ratpoints_extra_rank_{lower}")
            upsert_point(
                db, curve_id=curve_id, x=P[0], y=P[1],
                source="elkies_rank18_ratpoints", role="rigorous_witness",
                exact_verified=True, independence_status="rigorous_independent", rigorous_independent=True,
                search_ref="elkies2026:rank18-exact-extra", plugin_id=PLUGIN_ID,
                metadata={"certificate": cert.get("certificate")},
            )
            log_event(db, curve_id, "best", f"Elkies rank-18 exact search improves rigorous lower bound to {lower}")
            print(f"    >>> RIGOROUS LOWER BOUND NOW >= {lower}", flush=True)
        elif status == "dependent":
            upsert_point(
                db, curve_id=curve_id, x=P[0], y=P[1],
                source="elkies_rank18_ratpoints", role="candidate_extra",
                exact_verified=True, independence_status="dependent",
                search_ref="elkies2026:rank18-exact-dependent", plugin_id=PLUGIN_ID,
                metadata={"certificate": cert.get("certificate")},
            )

    row = get_curve(db, curve_id)
    if int(proven_lower(row)) >= BASELINE_RANK and row["status"] == "search_running":
        update_curve(db, curve_id, status="proven_lower")
    elif row["status"] == "search_running":
        update_curve(db, curve_id, status="screened")
    return {
        "curve_id": curve_id,
        "parameter": param,
        "variant": "rank18-first-cover",
        "rigorous_lower": int(proven_lower(get_curve(db, curve_id))),
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
        rp = probe_version(args.ratpoints)
    except RatpointsNotFound as exc:
        raise SystemExit(str(exc))
    rp_exe = rp["executable"]

    print("RANK HUNTER · ELKIES 2026 RANK-18 FIRST COVER", flush=True)
    print("=" * 68, flush=True)
    print(f"[db] {args.db}", flush=True)
    print(f"[ratpoints] {rp_exe}", flush=True)
    print("[baseline] 18 explicit exact cover sections", flush=True)
    print("[proof policy] specialization rank is promoted only by exact independence certificates", flush=True)

    if args.curve_id is not None:
        row = get_curve(db, args.curve_id)
        if row is None:
            raise SystemExit(f"curve #{args.curve_id} not found")
        if str(row["family"]) != FAMILY_NAME:
            raise SystemExit(f"curve #{args.curve_id} belongs to {row['family']!r}, not {FAMILY_NAME!r}")
        r = QQ(str(row["parameter"]))
        result = process_one(db, family, r, float(row["score"] or 0.0), args, rp_exe, existing_curve_id=int(row["id"]))
        print("RANK42_ELKIES_R18_SEARCH_RESULT=" + json.dumps(result or {}, sort_keys=True), flush=True)
        return

    rows = load_rows(args.input, args.limit)
    print(f"[queue] {len(rows)} candidates (input order preserved)", flush=True)
    for i, rec in enumerate(rows, 1):
        r = parameter_of(rec)
        score = float(rec.get("score") or 0.0)
        print(f"\n[{i}/{len(rows)}] r={r} score={score:.6f}", flush=True)
        existing = get_curve_by_key(db, FAMILY_NAME, str(r))
        if existing is not None and not args.force and str(existing["status"]) in {"proven_lower", "screened"}:
            print(f"    existing curve #{existing['id']} status={existing['status']}; preserving evidence and rerunning requested stages", flush=True)
        try:
            result = process_one(db, family, r, score, args, rp_exe, existing_curve_id=(int(existing["id"]) if existing else None))
            if result:
                print("    result: " + json.dumps(result, sort_keys=True), flush=True)
        except Exception as exc:
            if existing is not None:
                update_curve(db, int(existing["id"]), status="error", error=repr(exc))
            print(f"    ERROR: {exc!r}", flush=True)
        print(f"[candidate done] {i}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
