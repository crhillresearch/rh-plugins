import json
import os
import subprocess
import sys
from pathlib import Path

from rank42.candidates import create_pool, export_rows_jsonl, replace_pool_rows
from rank42.db import connect, upsert_curve
from rank42.plugin_geometry_result import (
    apply_plugin_geometry_result,
    validate_plugin_geometry_result,
)

from family import curve
from search_adapter import build_family_search_command, build_target_search_command


def _run(command, output, checkpoints):
    environment = {
        **os.environ,
        "RANK42_PLUGIN_GEOMETRY_RESULT_PATH": str(output),
        "RANK42_CHANNEL_CHECKPOINT_DIR": str(checkpoints),
        "RANK42_CHANNEL_CACHE_DIR": str(checkpoints.parent / "cache"),
    }
    subprocess.run(command, env=environment, check=True, timeout=40, capture_output=True, text=True)
    return validate_plugin_geometry_result(json.loads(output.read_text(encoding="utf-8")))


def test_family_target_and_core_exact_promotion(tmp_path):
    db_path = tmp_path / "scratch.db"
    db = connect(db_path)
    E = curve(4)
    curve_id = upsert_curve(
        db, family="C2 × C8 · Naskręcki channel family", parameter="4",
        a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]),
        plugin_id="c2xc8_channel_search", family_spec="c2xc8_channel_search",
    )
    pool = create_pool(db, name="channel-control", plugin_id="c2xc8_channel_search",
                       family_spec="c2xc8_channel_search")
    replace_pool_rows(db, pool["id"], [{"t": "4", "a": "4", "b": "1", "score": 1.0}])
    candidate = db.execute("SELECT * FROM candidates WHERE pool_id=?", (pool["id"],)).fetchone()
    db.execute("UPDATE candidates SET curve_id=? WHERE id=?", (curve_id, candidate["id"]))
    db.commit()
    candidate = db.execute("SELECT * FROM candidates WHERE id=?", (candidate["id"],)).fetchone()
    candidate_file = tmp_path / "candidate.jsonl"
    export_rows_jsonl(db, pool["id"], [candidate], candidate_file)
    settings = {"x_abs_max": 800, "z_max": 1, "max_points": 1000}

    family_result = _run(
        build_family_search_command(python=sys.executable, db=db_path,
                                    candidate_file=candidate_file, options=settings),
        tmp_path / "family-result.json", tmp_path / "checkpoints",
    )
    assert family_result["status"] == "completed"
    assert family_result["metadata"]["search_coverage"] == "bounded_complete"
    assert family_result["points"] == [["800", "448800"]]
    assert family_result["metadata"]["point_records"][0]["d"] == 2
    applied = apply_plugin_geometry_result(
        db, curve_id=curve_id, E=E, plugin_id="c2xc8_channel_search",
        result=family_result, search_ref="channel-integration-control",
        certificate_timeout=5, exact_candidates=2,
    )
    assert applied["exact_points_accepted"] == 1
    assert applied["rigorous_lower"] >= 1

    target_result = _run(
        build_target_search_command(python=sys.executable, db=db_path,
                                    curve_id=curve_id, options=settings),
        tmp_path / "target-result.json", tmp_path / "checkpoints",
    )
    assert target_result["points"] == family_result["points"]
    assert target_result["metadata"]["seed_set_fingerprint"] != family_result["metadata"]["seed_set_fingerprint"]
    assert (target_result["metadata"]["point_records"][0]["certification_attempt_fingerprint"]
            != family_result["metadata"]["point_records"][0]["certification_attempt_fingerprint"])
    db.close()


def test_target_rejects_foreign_curve_without_parameter_map(tmp_path):
    db_path = tmp_path / "scratch.db"
    db = connect(db_path)
    E = curve(4)
    curve_id = upsert_curve(
        db, family="foreign", parameter="4",
        a_invariants_json=json.dumps([str(a) for a in E.a_invariants()]),
        plugin_id="other_plugin",
    )
    result = _run(
        build_target_search_command(python=sys.executable, db=db_path,
                                    curve_id=curve_id, options={"x_abs_max": 800}),
        tmp_path / "foreign-result.json", tmp_path / "checkpoints",
    )
    assert result["status"] == "inconclusive"
    assert result["metadata"]["reason"] == "needs_verified_parameter_map"
    assert result["points"] == []
    db.close()


def test_target_maps_to_verified_minimal_model(tmp_path):
    db_path = tmp_path / "scratch.db"
    db = connect(db_path)
    source = curve(4)
    minimum = source.minimal_model()
    curve_id = upsert_curve(
        db, family="C2 × C8 · Naskręcki channel family", parameter="4",
        a_invariants_json=json.dumps([str(a) for a in minimum.a_invariants()]),
        plugin_id="c2xc8_channel_search", family_spec="c2xc8_channel_search",
    )
    result = _run(
        build_target_search_command(python=sys.executable, db=db_path,
                                    curve_id=curve_id,
                                    options={"x_abs_max": 800, "z_max": 1,
                                             "max_points": 1000}),
        tmp_path / "minimal-result.json", tmp_path / "checkpoints",
    )
    assert result["points"]
    assert result["metadata"]["model_isomorphism_urst"] != ["1", "0", "0", "0"]
    for x, y in result["points"]:
        minimum(x, y)
    db.close()


def test_inverse_parameter_reuses_completed_exact_scan(tmp_path):
    runner = str(Path(__file__).resolve().parents[1] / "search_runner.py")
    common = [sys.executable, runner, "--mode", "direct", "--x-abs-max", "800",
              "--z-max", "1", "--max-points", "1000"]
    first = _run(common + ["--parameter", "4"], tmp_path / "first.json",
                 tmp_path / "checkpoints")
    inverse = _run(common + ["--parameter", "1/4"], tmp_path / "inverse.json",
                   tmp_path / "checkpoints")
    assert first["metadata"]["completed_scan_cache_hit"] is False
    assert inverse["metadata"]["completed_scan_cache_hit"] is True
    assert first["points"] == inverse["points"]
