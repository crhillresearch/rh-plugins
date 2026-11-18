"""Family and target point-search adapter for Mazur torsion lanes."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def search_options(*, context="family", **_kwargs):
    if context not in {"family", "target"}:
        raise ValueError(f"unsupported search option context: {context!r}")
    manifest = json.loads((HERE / "plugin.json").read_text(encoding="utf-8"))
    return [dict(option) for option in manifest["search_options"][context]]


def _command(*, python, db, mode, source_flag, source_value, options):
    variant = str(options.get("plugin_variant") or "c10")
    command = [
        str(python), str(HERE / "search_runner.py"),
        "--db", str(db), "--mode", mode, "--variant", variant,
        source_flag, str(source_value),
        "--stages", str(options.get("stages") or (
            "1000,10000,100000" if mode == "family" else "1000,10000,100000,1000000"
        )),
        "--timeout", str(max(1, int(options.get("timeout", 30 if mode == "family" else 45)))),
        "--max-points", str(max(0, int(options.get("max_points", 64 if mode == "family" else 96)))),
        "--model-prep-timeout", str(max(0, int(options.get("model_prep_timeout", 15 if mode == "family" else 20)))),
    ]
    if options.get("ratpoints"):
        command += ["--ratpoints", str(options["ratpoints"])]
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
