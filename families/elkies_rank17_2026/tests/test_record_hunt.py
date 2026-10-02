from __future__ import annotations

import json

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_adapter():
    path = ROOT / "search_adapter.py"
    spec = importlib.util.spec_from_file_location("elkies_rank17_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_target_search_exposes_rank31_covering_funnel():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    options = {rec["key"]: rec for rec in manifest["search_options"]["target"]}
    assert "target_lower" not in options
    assert manifest["pipeline_search"]["target_rank"] == 31
    assert options["covering_search"]["default"] is True
    assert options["selmer_gate"]["default"] is True
    assert options["covering_engine"]["default"] == "simon_known"
    assert "mwrank_coverings" in options["covering_engine"]["choices"]
    assert options["covering_n_aux"]["default"] == 33
    assert options["covering_lim3"]["default"] >= 200
    assert options["exact_candidates"]["default"] >= 64


def test_family_search_keeps_expensive_coverings_opt_in():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    options = {rec["key"]: rec for rec in manifest["search_options"]["family"]}
    assert options["covering_search"]["default"] is False
    assert options["selmer_gate"]["default"] is False
    assert "target_lower" not in options
    assert manifest["pipeline_search"]["target_rank"] == 31


def test_record_hunt_runner_persists_rigorous_upper_bounds_and_certifies_growth():
    text = (ROOT / "family_search.py").read_text(encoding="utf-8")
    assert "mwrank_selmer" in text
    assert "_record_descent_upper" in text
    assert "pruned_by_selmer_upper" in text
    assert "run_covering_worker" in text
    assert "cert_points(E, trial" in text
    assert '"best_rigorous_lower"' in text
    assert "RANK42_ELKIES_SEARCH_RESULT=" in text


def test_covering_worker_is_classical_and_hard_timeout_parent_exists():
    worker = (ROOT / "covering_worker.py").read_text(encoding="utf-8")
    parent = (ROOT / "covering_search.py").read_text(encoding="utf-8")
    assert "mwrank_EllipticCurve" in worker
    assert "two_descent" in worker
    assert "simon_two_descent" in worker
    assert "known_points" in worker
    assert "subprocess.run" in parent
    assert "timeout=max(1, int(timeout))" in parent
    assert "CoveringSearchTimeout" in parent


def test_manifest_uses_primary_record_hunt_defaults():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.3.1"
    assert manifest["enabled_by_default"] is True
    defaults = manifest["candidate_defaults"]
    assert defaults["a_min"] == -5000
    assert defaults["a_max"] == 5000
    assert defaults["b_min"] == 1
    assert defaults["b_max"] == 1000
    assert defaults["stage_bounds"] == "1000,2000,4000"
    assert defaults["stage_keeps"] == "20000,4000,500"
    assert defaults["top"] == 500
