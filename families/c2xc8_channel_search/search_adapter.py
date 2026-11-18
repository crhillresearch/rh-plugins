"""Family/Target command adapter; core owns execution and point promotion."""
from __future__ import annotations

from pathlib import Path


RUNNER = Path(__file__).resolve().with_name("search_runner.py")
OPTION_DEFAULTS = {
    "generator": "squareclass", "x_abs_max": 2000, "z_max": 2,
    "k_max": 0, "max_points": 32, "max_candidates": 300000,
    "factor_timeout": 10, "run_timeout": 90,
    "modular_sieve": True, "torsion_orbit_dedupe": True,
    "require_full_factorization": True,
}


def _command(*, python, db, mode, source_flag, source_value, options):
    settings = {**OPTION_DEFAULTS, **dict(options or {})}
    command = [str(python), str(RUNNER), "--db", str(db),
               "--mode", mode, source_flag, str(source_value)]
    for key in ("generator", "x_abs_max", "z_max", "k_max", "max_points",
                "max_candidates", "factor_timeout", "run_timeout"):
        command.extend(("--" + key.replace("_", "-"), str(settings[key])))
    for key in ("modular_sieve", "torsion_orbit_dedupe", "require_full_factorization"):
        command.extend(("--" + key.replace("_", "-"),
                        "true" if settings[key] else "false"))
    return command


def build_family_search_command(*, python, db, candidate_file, options):
    return _command(python=python, db=db, mode="family",
                    source_flag="--input", source_value=candidate_file,
                    options=options)


def build_target_search_command(*, python, db, curve_id, options):
    return _command(python=python, db=db, mode="target",
                    source_flag="--curve-id", source_value=int(curve_id),
                    options=options)
