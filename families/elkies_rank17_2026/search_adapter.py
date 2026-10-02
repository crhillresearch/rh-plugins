"""Rank Hunter adapter for Elkies' published rank-17 K3 record hunt.

The ordinary Family Search remains cheap by default.  Target Search turns on
the classical record-hunt path: rigorous mwrank 2-Selmer gating followed by a
hard-timeout 2-covering search, with exact independence certification of every
promoted point.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY_SPEC = f"json:{HERE / 'family.json'}"
RUNNER = HERE / "family_search.py"


def _common(python, db, options):
    cmd = [
        str(python), str(RUNNER),
        "--db", str(db),
        "--family", FAMILY_SPEC,
        "--target-lower", str(int(options.get("target_lower", 31))),
        "--stages", str(options.get("stages", "1000,10000")),
        "--timeout", str(int(options.get("timeout", 15))),
        "--baseline-timeout", str(int(options.get("baseline_timeout", 120))),
        "--selmer-timeout", str(int(options.get("selmer_timeout", 180))),
        "--covering-timeout", str(int(options.get("covering_timeout", 900))),
        "--covering-engine", str(options.get("covering_engine", "simon_known")),
        "--covering-n-aux", str(int(options.get("covering_n_aux", 33))),
        "--covering-first-limit", str(int(options.get("covering_first_limit", 20))),
        "--covering-second-limit", str(int(options.get("covering_second_limit", 10))),
        "--covering-lim1", str(int(options.get("covering_lim1", 5))),
        "--covering-lim3", str(int(options.get("covering_lim3", 80))),
        "--exact-candidates", str(int(options.get("exact_candidates", 16))),
        "--certificate-timeout", str(int(options.get("certificate_timeout", 120))),
    ]
    if options.get("baseline_certificate"):
        cmd.append("--baseline-certificate")
    if options.get("covering_search"):
        cmd.append("--covering-search")
    if options.get("selmer_gate"):
        cmd.append("--selmer-gate")
    if options.get("ratpoints"):
        cmd += ["--ratpoints", str(options["ratpoints"])]
    if options.get("force"):
        cmd.append("--force")
    return cmd


def build_family_search_command(*, python, db, candidate_file, options):
    cmd = _common(python, db, options)
    cmd += ["--input", str(candidate_file), "--limit", str(int(options.get("limit", 20)))]
    return cmd


def build_target_search_command(*, python, db, curve_id, options):
    cmd = _common(python, db, options)
    cmd += ["--curve-id", str(int(curve_id))]
    return cmd
