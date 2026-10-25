"""Rank Hunter family and target search adapter for the Hill Rank-19 K3."""
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "search_runner.py"


def search_options(*, context="family", **_kwargs):
    if context not in {"family", "target"}:
        raise ValueError(f"unsupported search option context: {context!r}")
    manifest = json.loads((HERE / "plugin.json").read_text(encoding="utf-8"))
    return [dict(row) for row in manifest["search_options"][context]]


def _command(*, python, db, mode, source_flag, source_value, options):
    defaults = {
        "stages": "1000,10000,100000,1000000",
        "timeout": 30,
        "max_points": 64,
        "model_prep_timeout": 15,
    }
    command = [
        str(python), str(RUNNER), "--db", str(db), "--mode", mode,
        source_flag, str(source_value),
        "--stages", str(options.get("stages") or defaults["stages"]),
        "--timeout", str(int(options.get("timeout", defaults["timeout"]))),
        "--max-points", str(int(options.get("max_points", defaults["max_points"]))),
        "--model-prep-timeout", str(int(options.get(
            "model_prep_timeout", defaults["model_prep_timeout"]))),
    ]
    return command


def build_family_search_command(*, python, db, candidate_file, options):
    return _command(
        python=python, db=db, mode="family", source_flag="--input",
        source_value=candidate_file, options=options,
    )


def build_target_search_command(*, python, db, curve_id, options):
    return _command(
        python=python, db=db, mode="target", source_flag="--curve-id",
        source_value=int(curve_id), options=options,
    )
