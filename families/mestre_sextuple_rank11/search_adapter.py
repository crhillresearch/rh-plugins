"""Rank Hunter 0.9.2 adapter for the standalone Mestre sextuple plugin."""
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def search_options(*, context="family"):
    """Return the manifest-owned Family/Target option schema for core validation/UI."""
    if context not in {"family", "target"}:
        raise ValueError(f"unsupported search option context: {context!r}")
    manifest = json.loads((_ROOT / "plugin.json").read_text(encoding="utf-8"))
    return [dict(record) for record in manifest["search_options"][context]]


def _native(python, db, src_flag, src_value, o):
    cmd=[str(python), str(_ROOT / "native_search.py"), "--db", str(db), src_flag, str(src_value)]
    for key,flag in [
        ("limit","--limit"),("mode","--mode"),("stages","--stages"),("timeout","--timeout"),
        ("nonintegral_timeout","--nonintegral-timeout"),
        ("nonintegral_timeout_limit","--nonintegral-timeout-limit"),
        ("construction_timeout","--construction-timeout"),("subgroup_scan","--subgroup-scan"),
        ("exact_candidates","--exact-candidates"),("certificate_timeout","--certificate-timeout")]:
        if o.get(key) is not None:
            cmd += [flag, str(o[key])]
    if o.get("ratpoints"):
        cmd += ["--ratpoints", str(o["ratpoints"])]
    if o.get("force"):
        cmd.append("--force")
    return cmd


def _pgl2(python, db, src_flag, src_value, o):
    cmd=[str(python), str(_ROOT / "seeded_chart_search.py"), "--db", str(db), src_flag, str(src_value)]
    for key,flag in [
        ("limit","--limit"),("mode","--mode"),("charts","--charts"),
        ("chart_strategy","--chart-strategy"),("anchor_pool","--anchor-pool"),
        ("discovered_anchor_pool","--discovered-anchor-pool"),("free_bound","--free-bound"),
        ("exploratory_anchor_pool","--exploratory-anchor-pool"),
        ("exploratory_order","--exploratory-order"),
        ("exploratory_mix","--exploratory-mix"),
        ("stages","--stages"),("timeout","--timeout"),
        ("nonintegral_timeout","--nonintegral-timeout"),
        ("nonintegral_timeout_limit","--nonintegral-timeout-limit"),
        ("band_threshold","--band-threshold"),
        ("denominator_bands","--denominator-bands"),
        ("promotion_height","--promotion-height"),
        ("promotion_charts","--promotion-charts"),
        ("construction_timeout","--construction-timeout"),("subgroup_scan","--subgroup-scan"),
        ("exact_candidates","--exact-candidates"),("certificate_timeout","--certificate-timeout")]:
        if o.get(key) is not None:
            cmd += [flag, str(o[key])]
    if o.get("banded_rational"):
        cmd.append("--banded-rational")
    seed_curve_id = int(o.get("seed_curve_id") or 0)
    if seed_curve_id > 0:
        cmd += ["--seed-curve-id", str(seed_curve_id)]
    if o.get("ratpoints"):
        cmd += ["--ratpoints", str(o["ratpoints"])]
    if o.get("force"):
        cmd.append("--force")
    return cmd


def _build(python, db, src_flag, src_value, o):
    # A seed curve only has meaning in the seeded PGL2 worker.  Force that
    # path rather than silently ignoring the seed when the UI still shows
    # the broad-family default adapter as native.
    if int(o.get("seed_curve_id") or 0) > 0:
        return _pgl2(python, db, src_flag, src_value, o)
    return (_native if o.get("adapter") == "native" else _pgl2)(python, db, src_flag, src_value, o)


def build_family_search_command(*, python, db, candidate_file, options):
    return _build(python, db, "--input", candidate_file, options)


def build_target_search_command(*, python, db, curve_id, options):
    opts=dict(options); opts["limit"]=1
    return _build(python, db, "--id", curve_id, opts)
