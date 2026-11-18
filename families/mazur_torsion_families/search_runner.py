"""Write-free exact rational point search for prescribed-torsion families.

The runner only returns exact points. Rank Hunter core owns torsion gates,
independence certificates, and every rank promotion.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

from sage.all import EllipticCurve, QQ, sage_eval

from rank42.model_prep import ModelPrepFailure, ModelPrepTimeout, run_global_minimal_model
from rank42.plugin_geometry_result import RESULT_ENV, SCHEMA
from rank42.ratpoints import (
    RatpointsFailure, RatpointsNotFound, RatpointsTimeout,
    probe_version, run_ratpoints,
)
from rank42.search_models import completed_square_polynomial, recover_weierstrass_y

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "plugin.json").read_text(encoding="utf-8"))
VARIANTS = {str(item["id"]): item for item in MANIFEST["variants"]}
ENGINE_VERSION = "0.1.0"


def _stages(value):
    try:
        stages = sorted({int(part.strip()) for part in str(value).split(",") if part.strip()})
    except ValueError as exc:
        raise argparse.ArgumentTypeError("stages must be comma-separated positive integers") from exc
    if not stages or stages[0] <= 0:
        raise argparse.ArgumentTypeError("stages must be comma-separated positive integers")
    return stages


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--mode", choices=("family", "target"), required=True)
    parser.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--curve-id", type=int)
    parser.add_argument("--stages", type=_stages, default=_stages("1000,10000,100000"))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-points", type=int, default=64)
    parser.add_argument("--model-prep-timeout", type=int, default=15)
    parser.add_argument("--ratpoints")
    return parser.parse_args(argv)


def _candidate(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            return json.loads(line)
    raise ValueError("candidate input is empty")


def _family_curve(variant_id, parameter):
    variant = VARIANTS[str(variant_id)]
    family = variant["family"]
    if family.get("kind") != "json":
        raise ValueError(f"unsupported family definition kind for {variant_id}")
    definition = json.loads((HERE / family["file"]).read_text(encoding="utf-8"))
    name = str(definition.get("parameter") or "t")
    value = QQ(str(parameter))
    ainvs = [QQ(sage_eval(str(expr), locals={name: value})) for expr in definition["a_invariants"]]
    curve = EllipticCurve(QQ, ainvs)
    return None if curve.discriminant() == 0 else curve


def _subject(args):
    curve_id = None
    parameter = None
    if args.mode == "family":
        record = _candidate(args.input)
        candidate_id = int(record["_candidate_id"])
        parameter = record.get("t")
        if parameter is None and record.get("a") is not None and record.get("b") is not None:
            parameter = str(QQ(record["a"]) / QQ(record["b"]))
        with sqlite3.connect(str(args.db)) as con:
            row = con.execute("SELECT curve_id FROM candidates WHERE id=?", (candidate_id,)).fetchone()
        curve_id = None if row is None or row[0] is None else int(row[0])
        if parameter is None and curve_id is None:
            raise ValueError(f"candidate #{candidate_id} has neither a linked curve nor exact family parameter")
    else:
        curve_id = int(args.curve_id)

    with sqlite3.connect(str(args.db)) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT id, parameter, a_invariants_json FROM curves WHERE id=?", (curve_id,)
        ).fetchone()
    if row is not None and row["a_invariants_json"]:
        if parameter is None:
            parameter = row["parameter"]
        curve = EllipticCurve(QQ, [QQ(str(value)) for value in json.loads(row["a_invariants_json"])])
    elif args.mode == "family":
        curve = _family_curve(args.variant, parameter)
        if curve is None:
            raise ValueError(f"family specialization is singular at parameter {parameter}")
    else:
        raise ValueError(f"curve #{curve_id} has no stored Weierstrass model")
    return curve_id, None if parameter is None else QQ(str(parameter)), curve


def _key(point):
    negative = -point
    return min((str(point[0]), str(point[1])), (str(negative[0]), str(negative[1])))


def _search_model(curve, timeout):
    if int(timeout) <= 0:
        return curve, lambda point: curve(point), "stored", None
    try:
        prepared = run_global_minimal_model(curve.a_invariants(), timeout=max(1, int(timeout)))
        minimal = EllipticCurve(QQ, [QQ(str(value)) for value in prepared["a_invariants"]])
        iso = minimal.isomorphism_to(curve)
        return minimal, lambda point: iso(point), "minimal", float(prepared.get("runtime") or 0.0)
    except (ModelPrepFailure, ModelPrepTimeout, ArithmeticError, ValueError) as exc:
        return curve, lambda point: curve(point), "stored", repr(exc)


def build_result(args):
    curve_id, parameter, curve = _subject(args)
    points, seen, stages, partial = [], set(), [], False
    model, prep = "skipped", None
    if int(args.max_points) > 0:
        search_curve, to_stored, model, prep = _search_model(curve, args.model_prep_timeout)
        ainvs = list(search_curve.a_invariants())
        polynomial = completed_square_polynomial(ainvs)
        try:
            ratpoints = probe_version(args.ratpoints)
        except (RatpointsNotFound, RatpointsTimeout) as exc:
            ratpoints = None
            partial = True
            stages.append({"stage": None, "status": "ratpoints_unavailable", "error": repr(exc)})
        if ratpoints is not None:
            for height in args.stages:
                if len(points) >= int(args.max_points):
                    break
                try:
                    result = run_ratpoints(polynomial, int(height), executable=ratpoints["executable"], timeout=max(1, int(args.timeout)))
                except RatpointsTimeout as exc:
                    partial = True
                    stages.append({"stage": int(height), "status": "timeout", "error": repr(exc)})
                    continue
                except RatpointsFailure as exc:
                    partial = True
                    stages.append({"stage": int(height), "status": "error", "error": repr(exc)})
                    continue
                added = 0
                for raw in result["points"]:
                    if len(points) >= int(args.max_points):
                        break
                    try:
                        x = QQ(str(raw.x))
                        w = QQ(str(raw.y))
                        y = QQ(str(recover_weierstrass_y(ainvs, x, w)))
                        point = to_stored(search_curve(x, y))
                        point = curve(point[0], point[1])
                    except Exception:
                        continue
                    if point.is_zero():
                        continue
                    key = _key(point)
                    if key not in seen:
                        seen.add(key)
                        points.append(point)
                        added += 1
                stages.append({"stage": int(height), "status": "completed", "ratpoints_total": len(result["points"]), "new_exact": added})

    return {
        "schema": SCHEMA,
        "status": "partial" if partial else "completed",
        "engine": "mazur_torsion_exact_point_search",
        "engine_version": ENGINE_VERSION,
        "algorithm": "completed_square_ratpoints_with_exact_curve_mapping",
        "points": [[str(point[0]), str(point[1])] for point in points],
        "artifacts": [],
        "metadata": {
            "result_source": "typed_artifact",
            "plugin_id": "mazur_torsion_families",
            "variant": str(args.variant),
            "mode": str(args.mode),
            "curve_id": curve_id,
            "parameter": None if parameter is None else str(parameter),
            "ratpoints_points_returned": len(points),
            "search_model": model,
            "model_prep_detail": prep,
            "stages": stages,
            "torsion_family": VARIANTS[str(args.variant)]["torsion_groups"][0],
            "scientific_write_policy": "core_validated_artifacts_only",
        },
    }


def main(argv=None):
    args = parse_args(argv)
    result = build_result(args)
    output = os.environ.get(RESULT_ENV)
    if output:
        Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("MAZUR_TORSION_SEARCH_RESULT=" + json.dumps({
        "status": result["status"], "variant": args.variant,
        "points": len(result["points"]), "curve_id": result["metadata"]["curve_id"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
