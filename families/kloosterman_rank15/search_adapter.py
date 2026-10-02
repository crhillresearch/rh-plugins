"""Rank Hunter 0.9.2 adapter for Kloosterman's rank-15 K3.

The published rank-15 result is retained as historical plugin metadata only.
Because this package does not bundle an explicit 15-section basis/certificate,
Family Search deliberately disables generic-witness promotion and delegates
quick screening to Rank Hunter's current PARI-first auto-analysis pipeline.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY_SPEC = f"json:{HERE / 'family.json'}"


def build_family_search_command(*, python, db, candidate_file, options):
    family_spec = str(options.get("family_spec") or FAMILY_SPEC)
    return [
        str(python), "-m", "rank42.auto_analyze",
        "--db", str(db),
        "--input", str(candidate_file),
        "--family", family_spec,
        "--limit", str(int(options.get("limit", 20))),
        "--quick-strategy", str(options.get("primary_strategy", "pari")),
        "--quick-timeout", str(int(options.get("quick_timeout", 120))),
        "--fast-screen",
        "--quick-only",
        "--no-generic-witness",
    ]


def build_target_search_command(*, python, db, curve_id, options):
    cmd = [
        str(python), "-m", "rank42.fixed_curve_search",
        "--db", str(db),
        "--curve-id", str(int(curve_id)),
        "--stages", str(options.get("stages", "1000,10000,100000")),
        "--timeout", str(int(options.get("timeout", 20))),
        "--exact-candidates", str(int(options.get("exact_candidates", 8))),
        "--certificate-timeout", str(int(options.get("certificate_timeout", 120)))
    ]
    if options.get("ratpoints"):
        cmd += ["--ratpoints", str(options["ratpoints"])]
    return cmd
