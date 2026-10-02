"""Current Rank Hunter adapter for the standalone Kihara family plugin.

Only command construction lives here.  Mathematical/search logic is in the
plugin-local worker modules.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def _base(python, db, src_flag, src_value, options):
    cmd=[str(python), str(_ROOT / "chart_search.py"), "--db", str(db), src_flag, str(src_value)]
    for key,flag in [
        ("limit","--limit"),("charts","--charts"),("anchor_pool","--anchor-pool"),
        ("stages","--stages"),("timeout","--timeout"),
        ("height_timeout","--height-timeout"),("certificate_timeout","--certificate-timeout"),
        ("precision","--precision")]:
        if options.get(key) is not None:
            cmd += [flag, str(options[key])]
    if options.get("ratpoints"):
        cmd += ["--ratpoints", str(options["ratpoints"])]
    if options.get("include_known_fibers"):
        cmd.append("--include-known-fibers")
    if options.get("force"):
        cmd.append("--force")
    return cmd


def build_family_search_command(*, python, db, candidate_file, options):
    return _base(python, db, "--input", candidate_file, options)


def build_target_search_command(*, python, db, curve_id, options):
    opts=dict(options); opts["limit"]=1
    return _base(python, db, "--id", curve_id, opts)
