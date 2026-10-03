"""Rank Hunter Family/Target search adapter for Elkies X1092 Published MW17."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY_SPEC = "elkies_x1092_rank17_family"
RUNNER = HERE / "family_search.py"


def search_options(context="family"):
    target = str(context) == "target"
    return [
        {
            "key": "stages",
            "type": "str",
            "label": "ratpoints height stages",
            "default": "1000,10000,100000" if target else "1000,10000",
        },
        {
            "key": "timeout",
            "type": "int",
            "label": "Seconds per ratpoints stage",
            "default": 30 if target else 15,
            "min": 1,
            "max": 3600,
        },
        {
            "key": "baseline_certificate",
            "type": "bool",
            "label": "Certify specialized S1..S17 baseline",
            "default": True,
        },
        {
            "key": "baseline_timeout",
            "type": "int",
            "label": "Baseline certificate timeout",
            "default": 240 if target else 180,
            "min": 10,
            "max": 7200,
        },
        {
            "key": "exact_candidates",
            "type": "int",
            "label": "Exact extra-point candidates",
            "default": 32 if target else 8,
            "min": 0,
            "max": 512,
        },
        {
            "key": "certificate_timeout",
            "type": "int",
            "label": "Extra-point certificate timeout",
            "default": 300 if target else 180,
            "min": 10,
            "max": 14400,
        },
    ]


def _common(python, db, options):
    cmd = [
        str(python),
        str(RUNNER),
        "--db",
        str(db),
        "--family",
        FAMILY_SPEC,
        "--stages",
        str(options.get("stages", "1000,10000")),
        "--timeout",
        str(int(options.get("timeout", 15))),
        "--baseline-timeout",
        str(int(options.get("baseline_timeout", 180))),
        "--exact-candidates",
        str(int(options.get("exact_candidates", 8))),
        "--certificate-timeout",
        str(int(options.get("certificate_timeout", 180))),
    ]
    if options.get("baseline_certificate"):
        cmd.append("--baseline-certificate")
    if options.get("ratpoints"):
        cmd += ["--ratpoints", str(options["ratpoints"])]
    if options.get("force"):
        cmd.append("--force")
    return cmd


def build_family_search_command(*, python, db, candidate_file, options):
    cmd = _common(python, db, options)
    cmd += [
        "--input",
        str(candidate_file),
        "--limit",
        str(int(options.get("limit", 20))),
    ]
    return cmd


def build_target_search_command(*, python, db, curve_id, options):
    cmd = _common(python, db, options)
    cmd += ["--curve-id", str(int(curve_id))]
    return cmd
