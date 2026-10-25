"""Exact specialization sections plus an optional Ratpoints search."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

from sage.all import EllipticCurve, QQ

import family
from rank42.model_prep import (
    ModelPrepFailure,
    ModelPrepTimeout,
    run_global_minimal_model,
)
from rank42.plugin_geometry_result import RESULT_ENV, SCHEMA
from rank42.ratpoints import (
    RatpointsFailure,
    RatpointsNotFound,
    RatpointsTimeout,
    probe_version,
    run_ratpoints,
)
from rank42.search_models import completed_square_polynomial, recover_weierstrass_y


ENGINE_VERSION = "0.3.0"


def _stages(value):
    result = sorted({int(item.strip()) for item in str(value).split(",") if item.strip()})
    if not result or result[0] < 1:
        raise argparse.ArgumentTypeError("positive Ratpoints stages required")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--mode", choices=("family", "target"), required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--curve-id", type=int)
    parser.add_argument("--stages", type=_stages, default=_stages("1000,10000,100000,1000000"))
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
        parameter = None
        if args.mode == "family":
            candidate = _candidate(args.input)
            candidate_id = int(candidate["_candidate_id"])
            stored_candidate = connection.execute(
                "SELECT curve_id FROM candidates WHERE id=?", (candidate_id,)
            ).fetchone()
            raw_parameter = candidate.get("t")
            if raw_parameter is None:
                raw_parameter = QQ(candidate["a"]) / QQ(candidate["b"])
            parameter = QQ(str(raw_parameter))
            curve_id = (
                int(stored_candidate["curve_id"])
                if stored_candidate is not None and stored_candidate["curve_id"] is not None
                else None
            )
        else:
            curve_id = int(args.curve_id)

        row = None if curve_id is None else connection.execute(
            "SELECT id,parameter,a_invariants_json FROM curves WHERE id=?", (curve_id,)
        ).fetchone()
        if row is not None and row["a_invariants_json"]:
            if parameter is None:
                parameter = row["parameter"]
            E = EllipticCurve(QQ, [QQ(str(v)) for v in json.loads(row["a_invariants_json"])])
        elif args.mode == "family":
            # Pipeline candidate pools intentionally need not link their row to
            # a curve ID. The exact family parameter is sufficient to recreate
            # the same specialization used by the owning Pipeline candidate.
            E = family.curve(parameter)
            if E is None:
                raise ValueError(f"family specialization at n={parameter} is singular")
        else:
            raise ValueError(f"curve #{curve_id} is unavailable or lacks a model")
        return curve_id, parameter, E
    finally:
        connection.close()


def _point_key(point):
    opposite = -point
    return min((str(point[0]), str(point[1])), (str(opposite[0]), str(opposite[1])))


def _append(points, seen, point):
    if point.is_zero():
        return False
    key = _point_key(point)
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
        isomorphism = model.isomorphism_to(E)
        return model, lambda point: isomorphism(point), "minimal", prepared.get("runtime")
    except (ModelPrepFailure, ModelPrepTimeout, ArithmeticError, ValueError) as exc:
        return E, lambda point: E(point), "stored", repr(exc)


def build_result(args):
    curve_id, parameter, E = _subject(args)
    points, seen = [], set()
    section_error = None
    if args.mode == "family":
        try:
            for point in family.generic_section_points(parameter):
                _append(points, seen, E(point[0], point[1]))
        except Exception as exc:
            section_error = repr(exc)

    stages, stage_results = list(args.stages), []
    extra_count, partial = 0, bool(section_error)
    search_model = "skipped"
    preparation = None
    if int(args.max_points) > 0:
        search_curve, to_stored, search_model, preparation = _search_model(
            E, args.model_prep_timeout
        )
        ainvs = list(search_curve.a_invariants())
        polynomial = completed_square_polynomial(ainvs)
        try:
            ratpoints = probe_version(args.ratpoints)
        except (RatpointsNotFound, RatpointsTimeout) as exc:
            ratpoints = None
            partial = True
            stage_results.append({"stage": None, "status": "ratpoints_unavailable", "error": repr(exc)})
        if ratpoints is not None:
            for height in stages:
                if extra_count >= int(args.max_points):
                    break
                try:
                    result = run_ratpoints(
                        polynomial, height, executable=ratpoints["executable"],
                        timeout=max(1, int(args.timeout)),
                    )
                except RatpointsTimeout as exc:
                    partial = True
                    stage_results.append({"stage": height, "status": "timeout", "error": repr(exc)})
                    continue
                except RatpointsFailure as exc:
                    partial = True
                    stage_results.append({"stage": height, "status": "error", "error": repr(exc)})
                    continue
                added = 0
                for raw_point in result["points"]:
                    if extra_count >= int(args.max_points):
                        break
                    try:
                        x = QQ(str(raw_point.x))
                        y = QQ(str(recover_weierstrass_y(ainvs, x, QQ(str(raw_point.y)))))
                        mapped = to_stored(search_curve(x, y))
                        point = E(mapped[0], mapped[1])
                    except Exception:
                        continue
                    if _append(points, seen, point):
                        added += 1
                        extra_count += 1
                stage_results.append({
                    "stage": height,
                    "status": "completed",
                    "ratpoints_total": len(result["points"]),
                    "new_exact": added,
                })

    return {
        "schema": SCHEMA,
        "status": "partial" if partial else "completed",
        "engine": "hill_rank19_k3_specialization_search",
        "engine_version": ENGINE_VERSION,
        "algorithm": "paired_cover_section_specialization_plus_ratpoints",
        "points": [[str(point[0]), str(point[1])] for point in points],
        "artifacts": [],
        "metadata": {
            "result_source": "typed_artifact",
            "plugin_id": "hill_rank19_k3",
            "mode": args.mode,
            "curve_id": curve_id,
            "auxiliary_multiple": str(parameter) if args.mode == "family" else None,
            "paper_sections_returned": max(0, len(points) - extra_count) if args.mode == "family" else 0,
            "paper_section_error": section_error,
            "ratpoints_extras_returned": extra_count,
            "search_model": search_model,
            "model_prep_detail": preparation,
            "stages": stage_results,
            "rank_claim_boundary": (
                "Each specialized point is checked by core; generic rank 19 is not promoted to a fiber claim without exact independence."
            ),
            "scientific_write_policy": "core_validated_artifacts_only",
        },
    }


def main(argv=None):
    args = parse_args(argv)
    result = build_result(args)
    destination = os.environ.get(RESULT_ENV)
    if destination:
        Path(destination).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("HILL_RANK19_SEARCH_RESULT=" + json.dumps({
        "status": result["status"], "points": len(result["points"]),
        "curve_id": result["metadata"]["curve_id"],
        "paper_sections": result["metadata"]["paper_sections_returned"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
