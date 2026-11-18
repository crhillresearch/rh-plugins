"""Exact section and optional Ratpoints search for the C10 genus-one base change.

This runner is read-only. It returns point candidates through Rank Hunter's
typed plugin result boundary; core checks membership and certifies independence.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

from sage.all import EllipticCurve, QQ

import family
from rank42.model_points import map_points_exact
from rank42.model_prep import ModelPrepFailure, ModelPrepTimeout, run_global_minimal_model
from rank42.plugin_geometry_result import RESULT_ENV, SCHEMA
from rank42.ratpoints import RatpointsFailure, RatpointsNotFound, RatpointsTimeout, probe_version, run_ratpoints
from rank42.search_models import completed_square_polynomial, recover_weierstrass_y


ENGINE_VERSION = "0.1.0"


def _stages(value):
    rows = sorted({int(item.strip()) for item in str(value).split(",") if item.strip()})
    if not rows or rows[0] <= 0:
        raise argparse.ArgumentTypeError("positive Ratpoints stages required")
    return rows


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--mode", choices=("family", "target"), required=True)
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
            row = json.loads(line)
            if isinstance(row, dict):
                return row
            break
    raise ValueError("candidate input must contain a JSON object")


def _subject(args):
    connection = sqlite3.connect(str(args.db))
    connection.row_factory = sqlite3.Row
    try:
        if args.mode == "family":
            record = _candidate(args.input)
            parameter = record.get("t")
            if parameter is None:
                parameter = QQ(record["a"]) / QQ(record["b"])
            parameter = QQ(str(parameter))
            candidate_id = int(record["_candidate_id"])
            candidate = connection.execute(
                "SELECT curve_id FROM candidates WHERE id=?", (candidate_id,)
            ).fetchone()
            curve_id = None if candidate is None or candidate["curve_id"] is None else int(candidate["curve_id"])
        else:
            curve_id = int(args.curve_id)
            parameter = None

        row = None if curve_id is None else connection.execute(
            "SELECT id,parameter,a_invariants_json FROM curves WHERE id=?", (curve_id,)
        ).fetchone()
        if row is not None and row["a_invariants_json"]:
            if parameter is None:
                parameter = QQ(str(row["parameter"]))
            E = EllipticCurve(QQ, [QQ(str(value)) for value in json.loads(row["a_invariants_json"])])
        elif args.mode == "family":
            E = family.curve(parameter)
            if E is None:
                raise ValueError(f"no nonsingular family fiber at selector n={parameter}")
        else:
            raise ValueError(f"curve #{curve_id} is unavailable or has no stored model")
        return curve_id, parameter, E
    finally:
        connection.close()


def _key(point):
    opposite = -point
    return min((str(point[0]), str(point[1])), (str(opposite[0]), str(opposite[1])))


def _append(points, seen, point):
    if point.is_zero():
        return False
    key = _key(point)
    if key in seen:
        return False
    seen.add(key)
    points.append(point)
    return True


def _search_model(E, timeout):
    if int(timeout) <= 0:
        return E, lambda point: E(point), "stored", None
    try:
        prepared = run_global_minimal_model(E.a_invariants(), timeout=int(timeout))
        model = EllipticCurve(QQ, [QQ(str(value)) for value in prepared["a_invariants"]])
        iso = model.isomorphism_to(E)
        return model, lambda point: iso(point), "minimal", prepared.get("runtime")
    except (ModelPrepFailure, ModelPrepTimeout, ArithmeticError, ValueError) as exc:
        return E, lambda point: E(point), "stored", repr(exc)


def build_result(args):
    curve_id, index, E = _subject(args)
    points, seen = [], set()
    section_error = None
    try:
        construction_curve = family.curve(index)
        if construction_curve is None:
            raise ValueError("the selected family fiber is singular")
        exact_section = family.generic_section_points(index)
        for point in map_points_exact(construction_curve, E, exact_section):
            _append(points, seen, E(point[0], point[1]))
    except Exception as exc:
        section_error = repr(exc)

    stage_rows = []
    extra_count = 0
    partial = section_error is not None
    search_model_label, prep_detail = "skipped", None
    if int(args.max_points) > 0:
        search_curve, to_stored, search_model_label, prep_detail = _search_model(
            E, args.model_prep_timeout
        )
        ainvs = list(search_curve.a_invariants())
        polynomial = completed_square_polynomial(ainvs)
        try:
            ratpoints = probe_version(args.ratpoints)
        except (RatpointsNotFound, RatpointsTimeout) as exc:
            ratpoints = None
            partial = True
            stage_rows.append({"stage": None, "status": "ratpoints_unavailable", "error": repr(exc)})
        if ratpoints is not None:
            for height in args.stages:
                if extra_count >= int(args.max_points):
                    break
                try:
                    result = run_ratpoints(polynomial, int(height), executable=ratpoints["executable"],
                                           timeout=max(1, int(args.timeout)))
                except (RatpointsTimeout, RatpointsFailure) as exc:
                    partial = True
                    stage_rows.append({"stage": int(height), "status": "error", "error": repr(exc)})
                    continue
                added = 0
                for raw in result["points"]:
                    if extra_count >= int(args.max_points):
                        break
                    try:
                        x = QQ(str(raw.x))
                        w = QQ(str(raw.y))
                        y = QQ(str(recover_weierstrass_y(ainvs, x, w)))
                        image = to_stored(search_curve(x, y))
                        point = E(image[0], image[1])
                    except Exception:
                        continue
                    if _append(points, seen, point):
                        added += 1
                        extra_count += 1
                stage_rows.append({"stage": int(height), "status": "completed",
                                   "ratpoints_total": len(result["points"]), "new_exact": added})

    return {
        "schema": SCHEMA,
        "status": "partial" if partial else "completed",
        "engine": "c10_genus1_rank1_specialization_search",
        "engine_version": ENGINE_VERSION,
        "algorithm": "genus_one_base_section_plus_completed_square_ratpoints",
        "points": [[str(point[0]), str(point[1])] for point in points],
        "artifacts": [],
        "metadata": {
            "result_source": "typed_artifact",
            "plugin_id": "c10_genus1_rank1",
            "mode": str(args.mode),
            "curve_id": curve_id,
            "auxiliary_multiple": str(index),
            "generic_section_returned": section_error is None,
            "generic_section_error": section_error,
            "ratpoints_extras_returned": int(extra_count),
            "search_model": search_model_label,
            "model_prep_detail": prep_detail,
            "stages": stage_rows,
            "torsion_family": "Z/10Z",
            "parameter_base_genus": 1,
            "generic_rank_lower_bound": 1,
            "specialized_rank_claim": None,
            "scientific_write_policy": "core_validated_artifacts_only"
        }
    }


def main(argv=None):
    args = parse_args(argv)
    result = build_result(args)
    path = os.environ.get(RESULT_ENV)
    if path:
        Path(path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("HILL_RANK1_Z10_RESULT=" + json.dumps({
        "status": result["status"], "points": len(result["points"]),
        "mode": result["metadata"]["mode"], "curve_id": result["metadata"]["curve_id"]
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
