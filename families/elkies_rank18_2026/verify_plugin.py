#!/usr/bin/env python3
"""Static/no-DB integration checks for the rank-18 family plugin."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    manifest = json.loads((HERE / "plugin.json").read_text())
    assert manifest["id"] == "elkies_rank18_2026"
    assert manifest["version"] == "0.1.1"
    assert manifest["minimum_rank_hunter_version"] == "0.9.2"
    assert manifest["generic_rank"] == 18
    assert manifest["verified_generic_rank_lower"] == 18
    assert manifest["generic_rank_claim_state"] == "generic_lower_bound_verified"
    assert manifest["family"]["kind"] == "module"
    assert manifest["family"]["file"] == "rank18_family.py"
    assert manifest["search_adapter"] == "search_adapter.py"

    family = load_module("rh_elkies_rank18_family_verify", HERE / "rank18_family.py")
    symbolic = family.validate_symbolically()
    certificate = family.validate_generic_rank_claim()
    assert symbolic["sections_verified_on_curve"] == 18
    assert symbolic["recovered_p18_verified"] is True
    assert certificate["verified"] is True
    assert certificate["lower_bound"] == 18
    assert certificate["details"]["trace_identity_verified"] is True
    for value in (0, 1):
        points = family.generic_section_points(value)
        assert len(points) == 18
        assert all(P.curve() == family.curve(value) for P in points)

    adapter = load_module("rh_elkies_rank18_adapter_verify", HERE / "search_adapter.py")
    family_cmd = adapter.build_family_search_command(
        python="python", db="rank42.db", candidate_file="candidates.jsonl",
        options={"baseline_certificate": True, "limit": 1},
    )
    target_cmd = adapter.build_target_search_command(
        python="python", db="rank42.db", curve_id=123,
        options={"baseline_certificate": True},
    )
    assert str(HERE / "family_search.py") in family_cmd
    assert "--baseline-certificate" in family_cmd
    assert family_cmd[-4:] == ["--input", "candidates.jsonl", "--limit", "1"]
    assert target_cmd[-2:] == ["--curve-id", "123"]

    payload = {
        "schema": "rank-hunter.elkies-rank18-plugin-static-verification.v1",
        "status": "ok",
        "stage": "rank18_plugin_wiring_verified",
        "manifest_id": manifest["id"],
        "verified_generic_rank_lower": manifest["verified_generic_rank_lower"],
        "sections_verified": symbolic["sections_verified_on_curve"],
        "adapter_family_search": True,
        "adapter_target_search": True,
        "db_writes": False,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
