"""Write-free, one-fiber C2 × C8 channel worker for Rank Hunter."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import sqlite3
import time
from pathlib import Path

from sage.all import EllipticCurve, QQ

from channel_engine import ENGINE_VERSION, search
from family import canonical_parameter, curve


HERE = Path(__file__).resolve().parent
PLUGIN_ID = "c2xc8_channel_search"
RESULT_ENV = "RANK42_PLUGIN_GEOMETRY_RESULT_PATH"
SCHEMA = "rank42.plugin_geometry_result.v1"
STOP_REQUESTED = False


def _stop(_signum, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


def _bool(value):
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Exact C2 × C8 channel point search")
    parser.add_argument("--mode", choices=("family", "target", "direct"), required=True)
    parser.add_argument("--db")
    parser.add_argument("--input")
    parser.add_argument("--curve-id", type=int)
    parser.add_argument("--parameter")
    parser.add_argument("--generator", choices=("squareclass", "grid_control"), default="squareclass")
    for key, default in (("x_abs_max", 2000), ("z_max", 2), ("k_max", 0),
                         ("max_points", 32), ("max_candidates", 300000),
                         ("factor_timeout", 10), ("run_timeout", 90)):
        parser.add_argument("--" + key.replace("_", "-"), type=int, default=default)
    for key, default in (("modular_sieve", True), ("torsion_orbit_dedupe", True),
                         ("require_full_factorization", True)):
        parser.add_argument("--" + key.replace("_", "-"), type=_bool, default=default)
    args = parser.parse_args(argv)
    if args.mode == "family" and (not args.db or not args.input):
        parser.error("family mode requires --db and --input")
    if args.mode == "target" and (not args.db or args.curve_id is None):
        parser.error("target mode requires --db and --curve-id")
    if args.mode == "direct" and args.parameter is None:
        parser.error("direct mode requires --parameter")
    return args


def _source(args):
    if args.mode == "direct":
        t = QQ(args.parameter)
        return {"curve_id": None, "parameter": t, "stored": curve(t),
                "seed_set_fingerprint": None}

    con = sqlite3.connect(str(args.db))
    con.row_factory = sqlite3.Row
    try:
        if args.mode == "family":
            lines = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(lines) != 1:
                raise ValueError("Family Search host must supply one candidate per typed result")
            rec = lines[0]
            if rec.get("plugin_id") not in (None, PLUGIN_ID):
                raise ValueError("candidate belongs to a different Family plugin")
            candidate_id = int(rec["_candidate_id"])
            linked = con.execute("SELECT curve_id FROM candidates WHERE id=?", (candidate_id,)).fetchone()
            if linked is None or linked["curve_id"] is None:
                raise ValueError(f"candidate #{candidate_id} has no materialized curve")
            curve_id = int(linked["curve_id"])
            t = QQ(str(rec["t"]))
        else:
            curve_id = int(args.curve_id)
            t = None
        row = con.execute(
            "SELECT id,plugin_id,parameter,a_invariants_json FROM curves WHERE id=?",
            (curve_id,),
        ).fetchone()
        if row is None or not row["a_invariants_json"]:
            raise ValueError(f"curve #{curve_id} is unavailable or lacks a model")
        if row["plugin_id"] != PLUGIN_ID:
            return {"curve_id": curve_id, "parameter": None, "stored": None,
                    "unsupported": "needs_verified_parameter_map"}
        if t is None:
            t = QQ(str(row["parameter"]))
        E = EllipticCurve(QQ, [QQ(str(v)) for v in json.loads(row["a_invariants_json"])])
        seed_rows = con.execute(
            "SELECT x,y FROM points WHERE curve_id=? AND rigorous_independent=1 ORDER BY x,y",
            (curve_id,),
        ).fetchall()
        seed_blob = json.dumps([(r["x"], r["y"]) for r in seed_rows], sort_keys=True)
        seed_hash = hashlib.sha256(seed_blob.encode()).hexdigest()
        return {"curve_id": curve_id, "parameter": t, "stored": E,
                "seed_set_fingerprint": seed_hash}
    finally:
        con.close()


def _fingerprint(args, source):
    config = {
        "curve_id": source["curve_id"],
        "parameter": str(source["parameter"]), "model": [str(v) for v in source["stored"].a_invariants()],
        "generator": args.generator, "x_abs_max": args.x_abs_max,
        "z_max": args.z_max, "k_max": args.k_max,
        "modular_sieve": args.modular_sieve,
        "require_full_factorization": args.require_full_factorization,
        "engine_version": ENGINE_VERSION,
    }
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def _checkpoint_file(fingerprint):
    base = Path(os.environ.get("RANK42_CHANNEL_CHECKPOINT_DIR") or
                HERE.parents[2] / ".rank42-ui" / "channel-checkpoints")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{fingerprint}.json"


def _scan_cache_file(args, t, E):
    """Share a completed exact box across t, -t, 1/t and -1/t."""
    identity = {
        "canonical_parameter": [int(v) for v in canonical_parameter(t)],
        "model": [str(v) for v in E.a_invariants()],
        "generator": args.generator, "x_abs_max": args.x_abs_max,
        "z_max": args.z_max, "k_max": args.k_max,
        "max_points": args.max_points, "max_candidates": args.max_candidates,
        "modular_sieve": args.modular_sieve,
        "require_full_factorization": args.require_full_factorization,
        "engine_version": ENGINE_VERSION,
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    base = Path(os.environ.get("RANK42_CHANNEL_CACHE_DIR") or
                HERE.parents[2] / ".rank42-ui" / "channel-cache")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{key}.json", key


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _pair(P):
    return str(P[0]), str(P[1])


def _orbit_key(P, torsion):
    return min(_pair(S) for T in torsion for S in (P+T, -P+T) if not S.is_zero())


def build_result(args):
    source = _source(args)
    if source.get("unsupported"):
        return {
            "schema": SCHEMA, "status": "inconclusive", "engine": PLUGIN_ID,
            "engine_version": ENGINE_VERSION, "algorithm": "signed_squareclass_channel_search",
            "points": [], "artifacts": [],
            "metadata": {"reason": source["unsupported"], "curve_id": source["curve_id"]},
        }
    t = source["parameter"]
    E = curve(t)
    if E is None:
        raise ValueError(f"invalid C2 × C8 parameter {t}")
    stored = source["stored"]
    if not E.is_isomorphic(stored):
        return {
            "schema": SCHEMA, "status": "inconclusive", "engine": PLUGIN_ID,
            "engine_version": ENGINE_VERSION, "algorithm": "signed_squareclass_channel_search",
            "points": [], "artifacts": [],
            "metadata": {"reason": "stored_model_not_Q_isomorphic_to_parameter",
                         "curve_id": source["curve_id"], "parameter": str(t)},
        }
    iso = E.isomorphism_to(stored)
    fingerprint = _fingerprint(args, source)
    checkpoint_path = _checkpoint_file(fingerprint)
    cache_path, cache_key = _scan_cache_file(args, t, E)
    resume = None
    if checkpoint_path.exists():
        try:
            saved = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if saved.get("fingerprint") == fingerprint:
                resume = saved.get("engine_state")
        except (OSError, ValueError):
            pass

    def checkpoint(state):
        _write_json(checkpoint_path, {"fingerprint": fingerprint,
                                      "engine_state": state, "status": "partial"})
        current = time.monotonic()
        if (int(state.get("examined") or 0) - progress["examined"] >= 500
                or current - progress["at"] >= 5):
            progress.update({"examined": int(state.get("examined") or 0), "at": current})
            print(f"[channel] examined={progress['examined']} "
                  f"exact_points={len(state.get('points') or [])}", flush=True)

    progress = {"examined": 0, "at": time.monotonic()}
    print(f"[channel] t={t} model={list(E.a_invariants())} "
          f"generator={args.generator} |X|<={args.x_abs_max} Z<={args.z_max}",
          flush=True)
    scan = None
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("fingerprint") == cache_key and cached.get("scan", {}).get("status") == "completed":
                scan = cached["scan"]
        except (OSError, ValueError):
            pass
    cache_hit = scan is not None
    if cache_hit:
        print("[channel] reused completed exact scan for same-model parameter orbit", flush=True)
    if scan is None:
        scan = search(
            t, generator=args.generator, x_abs_max=args.x_abs_max, z_max=args.z_max,
            k_max=args.k_max, max_points=args.max_points,
            max_candidates=args.max_candidates, factor_timeout=args.factor_timeout,
            run_timeout=args.run_timeout, modular_sieve=args.modular_sieve,
            require_full_factorization=args.require_full_factorization,
            resume=resume, checkpoint=checkpoint, cancelled=lambda: STOP_REQUESTED,
        )
        if scan["status"] == "completed":
            _write_json(cache_path, {"fingerprint": cache_key, "scan": scan})
    if scan["status"] == "completed":
        checkpoint_path.unlink(missing_ok=True)
    elif not checkpoint_path.exists():
        checkpoint({"index": 0, "k": None, "z": 1,
                    "examined": scan["examined"], "points": scan["points"],
                    "factor": scan["factor"], "mode": args.generator})

    torsion = list(E.torsion_points())
    torsion_keys = {_pair(P) for P in torsion if not P.is_zero()}
    point_pairs, records, seen = [], [], set()
    proof_settings = {"certificate_timeout": getattr(args, "certificate_timeout", None)}
    for rec in scan["points"]:
        P = E(QQ(rec["x"]), QQ(rec["y"]))
        if _pair(P) in torsion_keys:
            continue
        key = _orbit_key(P, torsion) if args.torsion_orbit_dedupe else _pair(P)
        if args.torsion_orbit_dedupe and key in seen:
            continue
        seen.add(key)
        mapped = iso(P)
        mapped = stored(mapped[0], mapped[1])
        candidate_key = hashlib.sha256(json.dumps({
            "curve_id": source["curve_id"], "point": _pair(mapped),
            "model": [str(v) for v in stored.a_invariants()],
        }, sort_keys=True).encode()).hexdigest()
        attempt_key = hashlib.sha256(json.dumps({
            "candidate": candidate_key,
            "seed_set": source["seed_set_fingerprint"],
            "proof_settings": proof_settings,
        }, sort_keys=True).encode()).hexdigest()
        point_pairs.append(list(_pair(mapped)))
        records.append({**rec, "mapped_x": str(mapped[0]), "mapped_y": str(mapped[1]),
                        "orbit_key": list(key), "candidate_fingerprint": candidate_key,
                        "certification_attempt_fingerprint": attempt_key})
    return {
        "schema": SCHEMA, "status": scan["status"], "engine": PLUGIN_ID,
        "engine_version": ENGINE_VERSION,
        "algorithm": "signed_squareclass_channel_search" if args.generator == "squareclass" else "bounded_xz_grid_control",
        "points": point_pairs, "rigorous_upper_certificate": None, "artifacts": [],
        "metadata": {
            "result_source": "typed_artifact", "plugin_id": PLUGIN_ID,
            "curve_id": source["curve_id"], "parameter": str(t),
            "canonical_parameter": [int(v) for v in canonical_parameter(t)],
            "integral_model": [str(v) for v in E.a_invariants()],
            "stored_model": [str(v) for v in stored.a_invariants()],
            "model_map": "verified_Q_isomorphism",
            "model_isomorphism_urst": [str(v) for v in iso.tuple()],
            "factor": scan["factor"],
            "factorization_complete": bool(scan["factor"].get("complete")),
            "search_coverage": scan["coverage"], "reason": scan["reason"],
            "bounds": {"x_abs_max": args.x_abs_max, "z_max": args.z_max,
                       "k_max": args.k_max, "max_points": args.max_points,
                       "max_candidates": args.max_candidates,
                       "factor_timeout": args.factor_timeout,
                       "run_timeout": args.run_timeout},
            "examined": scan["examined"], "elapsed_seconds": scan["elapsed_seconds"],
            "point_records": records, "exact_points_before_orbit_dedupe": len(scan["points"]),
            "seed_set_fingerprint": source["seed_set_fingerprint"],
            "command_fingerprint": fingerprint,
            "completed_scan_cache_hit": cache_hit,
            "proof_status": "exact_point_only",
            "scientific_write_policy": "core_validated_artifacts_only",
        },
    }


def main(argv=None):
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    args = parse_args(argv)
    result = build_result(args)
    path = os.environ.get(RESULT_ENV)
    if path:
        _write_json(path, result)
    print("C2XC8_CHANNEL_RESULT=" + json.dumps({
        "status": result["status"], "points": len(result["points"]),
        "coverage": result["metadata"].get("search_coverage"),
        "reason": result["metadata"].get("reason"),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
