"""Write-free exact point search shared by DPT Z/6 rank-3 variants."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sqlite3
from pathlib import Path

from sage.all import EllipticCurve, QQ

from rank42.model_points import map_points_exact
from rank42.model_prep import ModelPrepFailure, ModelPrepTimeout, run_global_minimal_model
from rank42.plugin_geometry_result import RESULT_ENV, SCHEMA
from rank42.ratpoints import RatpointsFailure, RatpointsNotFound, RatpointsTimeout, probe_version, run_ratpoints
from rank42.search_models import completed_square_polynomial, recover_weierstrass_y

HERE = Path(__file__).resolve().parent
ENGINE_VERSION = "0.1.0"
VARIANT_FILES = {
    "lecacheux": HERE / "variants" / "lecacheux.py",
    "kihara": HERE / "variants" / "kihara.py",
    "eroshkin_plus": HERE / "variants" / "eroshkin_plus.py",
    "eroshkin_minus": HERE / "variants" / "eroshkin_minus.py",
    "dujella_peral": HERE / "variants" / "dujella_peral.py",
    "macleod": HERE / "variants" / "macleod.py",
}


def _load_variant(variant):
    path = VARIANT_FILES.get(str(variant))
    if path is None:
        raise ValueError(f"unknown DPT Z/6 variant: {variant!r}")
    spec = importlib.util.spec_from_file_location(f"dpt_z6_runner_{variant}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stages(text):
    values = sorted({int(piece.strip()) for piece in str(text).split(",") if piece.strip()})
    if not values or values[0] <= 0:
        raise argparse.ArgumentTypeError("positive comma-separated stages required")
    return values


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="DPT Z/6 rank-3 exact point search")
    ap.add_argument("--db", required=True)
    ap.add_argument("--mode", choices=["family", "target"], required=True)
    ap.add_argument("--variant", choices=sorted(VARIANT_FILES), required=True)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input")
    src.add_argument("--curve-id", type=int)
    ap.add_argument("--stages", type=_stages, default=_stages("1000,10000,100000"))
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--ratpoints")
    ap.add_argument("--max-points", type=int, default=32)
    ap.add_argument("--model-prep-timeout", type=int, default=10)
    ap.add_argument("--include-generic", action="store_true")
    return ap.parse_args(argv)


def _candidate_record(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if not isinstance(rec, dict):
                raise ValueError("candidate input must contain JSON objects")
            return rec
    raise ValueError("candidate input is empty")


def _subject(args):
    con = sqlite3.connect(str(args.db))
    con.row_factory = sqlite3.Row
    try:
        if args.mode == "family":
            rec = _candidate_record(args.input)
            cid = int(rec["_candidate_id"])
            candidate = con.execute("SELECT curve_id FROM candidates WHERE id=?", (cid,)).fetchone()
            if candidate is None or candidate["curve_id"] is None:
                raise ValueError(f"candidate #{cid} is not attached to a stored curve")
            curve_id = int(candidate["curve_id"])
            parameter = rec.get("t")
            if parameter is None and rec.get("a") is not None and rec.get("b") is not None:
                parameter = str(QQ(rec["a"]) / QQ(rec["b"]))
        else:
            curve_id = int(args.curve_id)
            parameter = None
        row = con.execute("SELECT id,parameter,a_invariants_json FROM curves WHERE id=?", (curve_id,)).fetchone()
        if row is None or not row["a_invariants_json"]:
            raise ValueError(f"curve #{curve_id} is unavailable or lacks a-invariants")
        if parameter is None:
            parameter = row["parameter"]
        E = EllipticCurve(QQ, [QQ(str(value)) for value in json.loads(row["a_invariants_json"])])
        return curve_id, QQ(str(parameter)), E
    finally:
        con.close()


def _point_key(P):
    Q = -P
    return min((str(P[0]), str(P[1])), (str(Q[0]), str(Q[1])))


def _append(points, seen, P):
    if P.is_zero():
        return False
    key = _point_key(P)
    if key in seen:
        return False
    seen.add(key)
    points.append(P)
    return True


def _search_model(E, timeout):
    timeout = int(timeout)
    if timeout <= 0:
        return E, (lambda P: E(P)), "stored", None
    try:
        prepared = run_global_minimal_model(E.a_invariants(), timeout=max(1, timeout))
        Em = EllipticCurve(QQ, [QQ(str(value)) for value in prepared["a_invariants"]])
        iso = Em.isomorphism_to(E)
        return Em, (lambda P: iso(P)), "minimal", float(prepared.get("runtime") or 0.0)
    except (ModelPrepFailure, ModelPrepTimeout, ArithmeticError, ValueError) as exc:
        return E, (lambda P: E(P)), "stored", repr(exc)


def build_result(args):
    family = _load_variant(args.variant)
    curve_id, parameter, E = _subject(args)
    points, seen = [], set()
    generic_count = 0
    generic_error = None
    if args.include_generic:
        try:
            Ef = family.curve(parameter)
            if Ef is None:
                raise ArithmeticError("variant specialization is singular")
            for P in map_points_exact(Ef, E, family.generic_section_points(parameter)):
                if _append(points, seen, P):
                    generic_count += 1
        except Exception as exc:
            generic_error = repr(exc)

    stage_rows = []
    extra_count = 0
    partial = False
    model_label = "skipped"
    prep_detail = None
    if int(args.max_points) > 0:
        search_curve, to_stored, model_label, prep_detail = _search_model(E, args.model_prep_timeout)
        ainvs = list(search_curve.a_invariants())
        poly = completed_square_polynomial(ainvs)
        try:
            rp = probe_version(args.ratpoints)
        except (RatpointsNotFound, RatpointsTimeout) as exc:
            rp = None
            partial = True
            stage_rows.append({"stage": None, "status": "ratpoints_unavailable", "error": repr(exc)})
        if rp is not None:
            for height in args.stages:
                if extra_count >= int(args.max_points):
                    break
                try:
                    result = run_ratpoints(poly, int(height), executable=rp["executable"], timeout=max(1, int(args.timeout)))
                except RatpointsTimeout as exc:
                    partial = True
                    stage_rows.append({"stage": int(height), "status": "timeout", "error": repr(exc)})
                    continue
                except RatpointsFailure as exc:
                    partial = True
                    stage_rows.append({"stage": int(height), "status": "error", "error": repr(exc)})
                    continue
                added = 0
                for raw in result["points"]:
                    if extra_count >= int(args.max_points):
                        break
                    try:
                        xq = QQ(str(raw.x)); wq = QQ(str(raw.y))
                        yq = QQ(str(recover_weierstrass_y(ainvs, xq, wq)))
                        P = to_stored(search_curve(xq, yq))
                        P = E(P[0], P[1])
                    except Exception:
                        continue
                    if _append(points, seen, P):
                        added += 1
                        extra_count += 1
                stage_rows.append({"stage": int(height), "status": "completed", "ratpoints_total": len(result["points"]), "new_exact": added})

    return {
        "schema": SCHEMA,
        "status": "partial" if partial else "completed",
        "engine": "dpt_z6_rank3_search",
        "engine_version": ENGINE_VERSION,
        "algorithm": "variant_published_basis_plus_completed_square_ratpoints",
        "points": [[str(P[0]), str(P[1])] for P in points],
        "artifacts": [],
        "metadata": {
            "result_source": "typed_artifact",
            "plugin_id": "dujella_peral_tadic_z6_rank3",
            "variant": str(args.variant),
            "mode": str(args.mode),
            "curve_id": int(curve_id),
            "parameter": str(parameter),
            "generic_sections_returned": int(generic_count),
            "generic_section_error": generic_error,
            "ratpoints_extras_returned": int(extra_count),
            "search_model": model_label,
            "model_prep_detail": prep_detail,
            "stages": stage_rows,
            "torsion_family": "C6",
            "scientific_write_policy": "core_validated_artifacts_only",
        },
    }


def main(argv=None):
    args = parse_args(argv)
    result = build_result(args)
    path = os.environ.get(RESULT_ENV)
    if path:
        Path(path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("DPT_Z6_SEARCH_RESULT=" + json.dumps({"status":result["status"],"variant":args.variant,"points":len(result["points"]),"curve_id":result["metadata"]["curve_id"]}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
