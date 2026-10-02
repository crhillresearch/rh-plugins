#!/usr/bin/env python3
"""Subgroup-aware search runner for the exact Elkies rank-17 K3 plugin.

Scientific policy:
* the published generic rank is metadata, not an automatic specialization claim;
* every specialized section is checked exactly by Sage when instantiated;
* a stored specialization lower bound is promoted only by Rank Hunter's exact
  quadratic-character independence certificate;
* ratpoints / 2-covering hits are mapped back exactly and never promoted by a numerical screen;
* an optional rigorous 2-Selmer upper bound may prune only the expensive rank-target
  covering stage; it never erases points or blocks the ordinary direct search;
* no ICARM lookup is automatic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _find_project_root():
    """Find the active Rank Hunter root without assuming plugin nesting depth."""
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
from covering_search import CoveringSearchFailure, CoveringSearchTimeout, run_covering_worker

PLUGIN_ID = "elkies_rank17_2026"
PLUGIN_VERSION = "1.3.1"
FAMILY_NAME = "Elkies 2026 elliptic K3, exact Mordell-Weil rank 17 over Q(t)"


def parse_stages(text):
    vals = sorted(set(int(x.strip()) for x in str(text).split(",") if x.strip()))
    if not vals or vals[0] <= 0:
        raise argparse.ArgumentTypeError("positive comma-separated stages required")
    return vals


def parse_args():
    ap = argparse.ArgumentParser(description="Elkies rank-17 subgroup-aware family search")
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
    ap.add_argument("--baseline-timeout", type=int, default=120)
    ap.add_argument("--exact-candidates", type=int, default=8)
    ap.add_argument("--certificate-timeout", type=int, default=120)
    ap.add_argument("--target-lower", type=int, default=31, help="research target used only by the rigorous Selmer gate")
    ap.add_argument("--covering-search", action="store_true", help="run classical 2-covering point search after direct ratpoints")
    ap.add_argument("--covering-engine", choices=("simon_known", "mwrank_coverings"), default="simon_known")
    ap.add_argument("--selmer-gate", action="store_true", help="run mwrank selmer-only 2-descent before deep covering search")
    ap.add_argument("--selmer-timeout", type=int, default=180)
    ap.add_argument("--covering-timeout", type=int, default=900)
    ap.add_argument("--covering-first-limit", type=int, default=20)
    ap.add_argument("--covering-second-limit", type=int, default=10)
    ap.add_argument("--covering-n-aux", type=int, default=33)
    ap.add_argument("--covering-lim1", type=int, default=5)
    ap.add_argument("--covering-lim3", type=int, default=80)
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def point_key(P):
    Q = -P
    a = (QQ(P[0]), QQ(P[1]))
    b = (QQ(Q[0]), QQ(Q[1]))
    return min(a, b)


def parameter_of(row):
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
    """Write an exact independent-subgroup certificate to Rank Hunter evidence."""
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
            source="elkies_published_section",
            role="rigorous_witness" if rigorous else "generic_section",
            exact_verified=True,
            independence_status="rigorous_independent" if rigorous else "unknown",
            rigorous_independent=rigorous,
            search_ref="elkies2026:published-basis",
            plugin_id=PLUGIN_ID,
            metadata={
                "section_label": f"P{idx:02d}",
                "published_generic_height": 4,
                "certificate": certificate if rigorous else None,
            },
        )


def certify_baseline(db, curve_id, E, baseline, timeout):
    try:
        cert = cert_points(E, baseline, timeout)
    except (ExactCertificateTimeout, ExactCertificateFailure) as exc:
        log_event(db, curve_id, "warn", f"Elkies 17-section baseline certificate inconclusive: {exc}")
        print(f"    baseline exact certificate INCONCLUSIVE: {exc}", flush=True)
        return False, None
    if cert.get("independent"):
        current = get_curve(db, curve_id)
        prior_descent = int(current["descent_lower"] or 0)
        fields = {
            "generic_lower": max(17, int(current["generic_lower"] or 0)),
            "status": "proven_lower",
            "error": None,
        }
        # Do not overwrite a previously certified higher-rank witness basis.
        if prior_descent <= 17:
            fields["descent_lower"] = 17
            fields["generators_json"] = json.dumps([[str(P[0]), str(P[1])] for P in baseline])
        update_curve(db, curve_id, **fields)
        record_subgroup_evidence(db, curve_id, E, baseline, cert, source="published_baseline")
        save_baseline_points(db, curve_id, baseline, rigorous=True, certificate=cert.get("certificate"))
        log_event(db, curve_id, "info", "exact specialized Elkies baseline certified rank >=17")
        print(f"    baseline CERTIFIED: rank >=17 ({cert.get('runtime_seconds',0):.2f}s)", flush=True)
        return True, cert
    if cert.get("status") == "dependent":
        update_curve(db, curve_id, status="baseline_dependent", error="published sections specialize dependently at this parameter")
        log_event(db, curve_id, "warn", "published Elkies sections specialize dependently")
        print("    baseline exactly DEPENDENT at this specialization", flush=True)
        return False, cert
    print("    baseline exact certificate inconclusive", flush=True)
    return False, cert


def _record_descent_upper(db, curve_id, E, result, *, source, options):
    """Persist a completed rigorous descent upper bound without changing lower evidence."""
    upper = result.get("rigorous_upper")
    if upper is None:
        return None
    record_rank_evidence(
        db,
        curve_id=int(curve_id),
        model=[str(a) for a in E.a_invariants()],
        data={
            "engine": str(source),
            "evidence_type": "descent",
            "status": "completed",
            "rigorous": True,
            "rigorous_lower": None,
            "rigorous_upper": int(upper),
            "exact_rank": None,
            "assumptions": [],
            "points_found": list(result.get("points") or []),
            "minimal_model_a_invariants": result.get("minimal_model_a_invariants"),
            "options": {
                "plugin_id": PLUGIN_ID,
                "plugin_version": PLUGIN_VERSION,
                **dict(options or {}),
            },
            "elapsed_seconds": result.get("runtime_seconds"),
            "stdout_summary": json.dumps(result, sort_keys=True),
        },
    )
    return apply_reduced_rank_state(db, int(curve_id))


def _run_selmer_gate(db, curve_id, E, rigorous_basis, args):
    if not args.selmer_gate:
        return {"status": "disabled", "pass": True, "upper": None}
    print(
        f"    [selmer gate] mwrank 2-Selmer upper bound; target >= {int(args.target_lower)} "
        f"n_aux={int(args.covering_n_aux)}",
        flush=True,
    )
    try:
        result = run_covering_worker(
            E.a_invariants(),
            rigorous_basis,
            mode="mwrank_selmer",
            timeout=int(args.selmer_timeout),
            first_limit=int(args.covering_first_limit),
            second_limit=int(args.covering_second_limit),
            n_aux=int(args.covering_n_aux),
        )
    except CoveringSearchTimeout as exc:
        print(f"    [selmer gate] TIMEOUT: {exc}; deep covering search remains eligible", flush=True)
        return {"status": "timeout", "pass": True, "upper": None, "error": str(exc)}
    except CoveringSearchFailure as exc:
        print(f"    [selmer gate] ERROR: {exc}; deep covering search remains eligible", flush=True)
        return {"status": "error", "pass": True, "upper": None, "error": str(exc)}

    upper = int(result["rigorous_upper"])
    current_lower = int(proven_lower(get_curve(db, int(curve_id))))
    state = _record_descent_upper(
        db,
        curve_id,
        E,
        result,
        source="eclib_mwrank_selmer_gate",
        options={
            "target_lower": int(args.target_lower),
            "first_limit": int(args.covering_first_limit),
            "second_limit": int(args.covering_second_limit),
            "n_aux": int(args.covering_n_aux),
        },
    )
    if upper < current_lower:
        print(
            f"    [selmer gate] EVIDENCE CONFLICT upper={upper} < stored lower={current_lower}; "
            "not pruning candidate",
            flush=True,
        )
        return {
            "status": "conflict",
            "pass": True,
            "upper": upper,
            "stored_lower": current_lower,
            "state": state,
        }
    passed = upper >= int(args.target_lower)
    print(
        f"    [selmer gate] rigorous upper <= {upper}; "
        + ("PASS" if passed else f"PRUNE FOR RANK-{int(args.target_lower)} COVERING SEARCH"),
        flush=True,
    )
    return {
        "status": "pass" if passed else "below_target",
        "pass": bool(passed),
        "upper": upper,
        "stored_lower": current_lower,
        "state": state,
    }


def _search_classical_coverings(db, curve_id, E, rigorous_basis, args):
    """Search quartic 2-coverings with a hard timeout and return exact E(Q) points."""
    if not args.covering_search:
        return [], {"status": "disabled", "engine": None, "upper": None}

    gate = _run_selmer_gate(db, curve_id, E, rigorous_basis, args)
    if not gate.get("pass", True):
        return [], {
            "status": "pruned_by_selmer_upper",
            "engine": None,
            "upper": gate.get("upper"),
            "gate": gate,
        }

    mode = str(args.covering_engine)
    print(
        f"    [2-coverings] engine={mode} timeout={int(args.covering_timeout)}s "
        f"known_basis={len(rigorous_basis)}",
        flush=True,
    )
    try:
        result = run_covering_worker(
            E.a_invariants(),
            rigorous_basis,
            mode=mode,
            timeout=int(args.covering_timeout),
            first_limit=int(args.covering_first_limit),
            second_limit=int(args.covering_second_limit),
            n_aux=int(args.covering_n_aux),
            lim1=int(args.covering_lim1),
            lim3=int(args.covering_lim3),
        )
    except CoveringSearchTimeout as exc:
        print(f"    [2-coverings] TIMEOUT: {exc}", flush=True)
        return [], {"status": "timeout", "engine": mode, "upper": gate.get("upper"), "gate": gate, "error": str(exc)}
    except CoveringSearchFailure as exc:
        print(f"    [2-coverings] ERROR: {exc}", flush=True)
        return [], {"status": "error", "engine": mode, "upper": gate.get("upper"), "gate": gate, "error": str(exc)}

    source = "simon_two_descent_known_points" if mode == "simon_known" else "eclib_mwrank_full_two_descent"
    state = _record_descent_upper(
        db,
        curve_id,
        E,
        result,
        source=source,
        options={
            "target_lower": int(args.target_lower),
            "covering_engine": mode,
            "known_basis_size": len(rigorous_basis),
            "first_limit": int(args.covering_first_limit),
            "second_limit": int(args.covering_second_limit),
            "n_aux": int(args.covering_n_aux),
            "lim1": int(args.covering_lim1),
            "lim3": int(args.covering_lim3),
        },
    )

    points = []
    seen = set()
    for xy in result.get("points") or []:
        try:
            P = E(QQ(str(xy[0])), QQ(str(xy[1])))
        except Exception:
            continue
        if P.is_zero():
            continue
        key = point_key(P)
        if key in seen:
            continue
        seen.add(key)
        points.append(P)
    print(
        f"    [2-coverings] completed upper={result.get('rigorous_upper')} "
        f"exact_points={len(points)} runtime={float(result.get('runtime_seconds') or 0):.2f}s",
        flush=True,
    )
    return points, {
        "status": "completed",
        "engine": mode,
        "upper": result.get("rigorous_upper"),
        "descent_lower": result.get("descent_lower"),
        "points": len(points),
        "gate": gate,
        "state": state,
        "runtime_seconds": result.get("runtime_seconds"),
    }


def search_ratpoints(E, stages, executable, timeout):
    Es = E.short_weierstrass_model()
    iso = Es.isomorphism_to(E)
    ainvs = list(Es.a_invariants())
    if any(ainvs[i] != 0 for i in (0,1,2)):
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
                Ps = Es(QQ(str(q.x)), QQ(str(q.y)))
                P = iso(Ps)
            except Exception:
                continue
            if P.is_zero():
                continue
            k = point_key(P)
            if k in found:
                continue
            found[k] = P
            added += 1
        print(f"    [ratpoints] H={H} raw={len(res['points'])} new_exact={added} total={len(found)} runtime={res['runtime']:.2f}s", flush=True)
    return list(found.values())


def process_one(db, family, t, score, args, rp_exe, existing_curve_id=None):
    param = str(t)
    E = family.curve(t)
    if E is None:
        print("    singular/undefined specialization", flush=True)
        return None
    baseline = family.generic_section_points(t)
    if len(baseline) != 17:
        raise RuntimeError(f"expected 17 published specialized sections, got {len(baseline)}")

    curve_id = existing_curve_id or upsert_curve(db, family=FAMILY_NAME, parameter=param, score=score)
    update_curve(
        db, curve_id,
        a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]),
        status="search_running",
        error=None,
    )
    save_baseline_points(db, curve_id, baseline, rigorous=False)

    baseline_ok = int(proven_lower(get_curve(db, curve_id))) >= 17
    if args.baseline_certificate and (args.force or not baseline_ok):
        baseline_ok, _ = certify_baseline(db, curve_id, E, baseline, args.baseline_timeout)
    elif baseline_ok:
        print(f"    stored rigorous baseline >= {proven_lower(get_curve(db, curve_id))}", flush=True)
    else:
        print("    specialized baseline stored exact-on-curve but not independently certified", flush=True)

    rigorous_basis = list(baseline)
    if int(proven_lower(get_curve(db, curve_id))) > 17:
        # Existing rigorous generators may already include extras. Rehydrate them
        # before covering search so known-point descent sees the strongest subgroup.
        row = get_curve(db, curve_id)
        try:
            stored = json.loads(row["generators_json"] or "[]")
            if len(stored) >= int(row["descent_lower"] or 0) > 17:
                rigorous_basis = [E(QQ(str(x)), QQ(str(y))) for x,y in stored[:int(row["descent_lower"])]]
        except Exception:
            rigorous_basis = list(baseline)

    direct_found = search_ratpoints(E, args.stages, rp_exe, args.timeout)
    covering_found, covering_info = _search_classical_coverings(
        db, curve_id, E, rigorous_basis, args
    )

    baseline_keys = {point_key(P) for P in baseline}
    known_keys = {point_key(P) for P in rigorous_basis}
    found_by_key = {}
    source_by_key = {}
    for P in direct_found:
        key = point_key(P)
        found_by_key[key] = P
        source_by_key[key] = "elkies_ratpoints"
    for P in covering_found:
        key = point_key(P)
        found_by_key[key] = P
        source_by_key[key] = f"elkies_2covering_{args.covering_engine}"
    found = list(found_by_key.values())

    candidate_points = []
    for key, P in found_by_key.items():
        if key in baseline_keys or key in known_keys:
            continue
        candidate_points.append(P)
        point_source = source_by_key[key]
        upsert_point(
            db, curve_id=curve_id, x=P[0], y=P[1],
            source=point_source, role="candidate_extra",
            exact_verified=True, independence_status="unknown",
            search_ref=("elkies2026:2-coverings" if point_source.startswith("elkies_2covering_") else "elkies2026:ratpoints"),
            plugin_id=PLUGIN_ID,
            metadata={
                "covering_engine": args.covering_engine if point_source.startswith("elkies_2covering_") else None,
                "search_class": "classical_2_covering" if point_source.startswith("elkies_2covering_") else "direct_ratpoints",
            },
        )
    print(
        f"    exact hits outside current rigorous subgroup = {len(candidate_points)} "
        f"(direct={len(direct_found)} covering={len(covering_found)})",
        flush=True,
    )

    accepted = []
    exact_attempts = 0
    for P in candidate_points:
        if exact_attempts >= max(0, int(args.exact_candidates)):
            break
        pkey = point_key(P)
        if pkey in known_keys:
            continue
        point_source = source_by_key.get(pkey, "elkies_ratpoints")
        point_search_ref = (
            "elkies2026:2-coverings"
            if point_source.startswith("elkies_2covering_")
            else "elkies2026:ratpoints"
        )
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
                generic_lower=max(17, int(get_curve(db,curve_id)["generic_lower"] or 0)),
                descent_lower=lower,
                generators_json=json.dumps([[str(Q[0]),str(Q[1])] for Q in rigorous_basis]),
                status="proven_lower",
                error=None,
            )
            record_subgroup_evidence(
                db,
                curve_id,
                E,
                rigorous_basis,
                cert,
                source=f"{point_source}_extra_rank_{lower}",
            )
            upsert_point(
                db, curve_id=curve_id, x=P[0], y=P[1],
                source=point_source, role="rigorous_witness",
                exact_verified=True, independence_status="rigorous_independent",
                rigorous_independent=True, search_ref=point_search_ref,
                plugin_id=PLUGIN_ID,
                metadata={
                    "certificate": cert.get("certificate"),
                    "covering_engine": args.covering_engine if point_source.startswith("elkies_2covering_") else None,
                },
            )
            log_event(db, curve_id, "best", f"Elkies exact search improves rigorous lower bound to {lower}")
            print(f"    >>> RIGOROUS LOWER BOUND NOW >= {lower}", flush=True)
        elif status == "dependent":
            upsert_point(
                db, curve_id=curve_id, x=P[0], y=P[1],
                source=point_source, role="candidate_extra",
                exact_verified=True, independence_status="dependent",
                search_ref=point_search_ref, plugin_id=PLUGIN_ID,
                metadata={
                    "certificate": cert.get("certificate"),
                    "covering_engine": args.covering_engine if point_source.startswith("elkies_2covering_") else None,
                },
            )

    row = get_curve(db, curve_id)
    if int(proven_lower(row)) >= 17 and row["status"] == "search_running":
        update_curve(db, curve_id, status="proven_lower")
    elif row["status"] == "search_running":
        update_curve(db, curve_id, status="screened")
    rigorous_lower = int(proven_lower(get_curve(db, curve_id)))
    return {
        "curve_id": curve_id,
        "parameter": param,
        "rigorous_lower": rigorous_lower,
        "best_rigorous_lower": rigorous_lower,
        "ratpoints_exact": len(direct_found),
        "covering_exact": len(covering_found),
        "covering_status": covering_info.get("status"),
        "covering_engine": covering_info.get("engine"),
        "selmer_upper": (covering_info.get("gate") or {}).get("upper"),
        "covering_upper": covering_info.get("upper"),
        "candidate_extras": len(candidate_points),
        "mapped_extra_points": len(candidate_points),
        "exact_attempts": exact_attempts,
        "accepted_extras": len(accepted),
        "rigorous_hits": len(accepted),
        "target_lower": int(args.target_lower),
    }


def main():
    args = parse_args()
    db = connect(args.db)
    family = load_family(args.family, need_sections=True)
    if family.name() != "Elkies 2026 rank-17 K3":
        raise SystemExit(f"unexpected family {family.name()!r}")
    try:
        rp = probe_version(args.ratpoints)
    except RatpointsNotFound as exc:
        raise SystemExit(str(exc))
    rp_exe = rp["executable"]

    print("RANK HUNTER · ELKIES 2026 RANK-17 K3", flush=True)
    print("="*68, flush=True)
    print(f"[db] {args.db}", flush=True)
    print(f"[ratpoints] {rp_exe}", flush=True)
    print("[proof policy] rank is promoted only by exact independence certificates", flush=True)
    print(
        f"[record hunt] target>={int(args.target_lower)} covering_search={bool(args.covering_search)} "
        f"engine={args.covering_engine} selmer_gate={bool(args.selmer_gate)}",
        flush=True,
    )

    if args.curve_id is not None:
        row = get_curve(db, args.curve_id)
        if row is None:
            raise SystemExit(f"curve #{args.curve_id} not found")
        if str(row["family"]) != FAMILY_NAME:
            raise SystemExit(f"curve #{args.curve_id} belongs to {row['family']!r}, not the Elkies plugin family")
        t = QQ(str(row["parameter"]))
        result = process_one(db, family, t, float(row["score"] or 0.0), args, rp_exe, existing_curve_id=int(row["id"]))
        print("RANK42_ELKIES_SEARCH_RESULT=" + json.dumps(result or {}, sort_keys=True), flush=True)
        return

    rows = load_rows(args.input, args.limit)
    print(f"[queue] {len(rows)} candidates (input order preserved)", flush=True)
    completed_results = []
    for i, rec in enumerate(rows, 1):
        t = parameter_of(rec)
        score = float(rec.get("score") or 0.0)
        print(f"\n[{i}/{len(rows)}] t={t} score={score:.6f}", flush=True)
        existing = get_curve_by_key(db, FAMILY_NAME, str(t))
        if existing is not None and not args.force and str(existing["status"]) in {"proven_lower","screened"}:
            print(f"    existing curve #{existing['id']} status={existing['status']}; re-searching point stages without deleting evidence", flush=True)
        try:
            result = process_one(db, family, t, score, args, rp_exe, existing_curve_id=(int(existing["id"]) if existing else None))
            if result:
                completed_results.append(result)
                print("    result: " + json.dumps(result, sort_keys=True), flush=True)
        except Exception as exc:
            if existing is not None:
                update_curve(db, int(existing["id"]), status="error", error=repr(exc))
            print(f"    ERROR: {exc!r}", flush=True)
        print(f"[candidate done] {i}/{len(rows)}", flush=True)

    summary = {
        "status": "ELKIES RANK-17 RECORD HUNT COMPLETE",
        "candidates_planned": len(rows),
        "candidates_completed": len(completed_results),
        "best_rigorous_lower": max([17, *[int(r.get("rigorous_lower") or 0) for r in completed_results]]),
        "mapped_extra_points": sum(int(r.get("candidate_extras") or 0) for r in completed_results),
        "covering_exact": sum(int(r.get("covering_exact") or 0) for r in completed_results),
        "rigorous_hits": sum(int(r.get("accepted_extras") or 0) for r in completed_results),
        "target_lower": int(args.target_lower),
        "covering_engine": args.covering_engine if args.covering_search else None,
        "selmer_gate": bool(args.selmer_gate),
    }
    print("RANK42_ELKIES_SEARCH_RESULT=" + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
