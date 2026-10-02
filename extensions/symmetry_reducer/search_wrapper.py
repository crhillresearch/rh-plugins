#!/usr/bin/env python3
"""Transparent exact source-height PGL2 chart symmetry wrapper.

Supported workers:
  * Campbell: ``rank42.mobius_quartic.build_chart_plan``
  * Mestre/Fermigier: ``rank42.mobius_quartic.build_chart_plan``
  * Kihara: ``rank42.mobius_quartic.rank_charts``

The family plugins are not edited.  The wrapper patches the shared planner
symbols before importing/running the family worker, so later ``from ... import``
statements receive the wrapped planner.

Two plan policies exist:
  * dedup  -- keep the first/highest-ranked representative from each exact
              source-height orbit in the originally requested pool.
  * refill -- search farther down the ranked candidate pool until the requested
              number of distinct representatives is obtained, where possible.

The latter changes coverage intentionally; it is not an A/B-equivalent run.
"""
from __future__ import annotations

import argparse
import importlib
import json
import runpy
import sys
from fractions import Fraction
from functools import reduce
from math import gcd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import rank42.mobius_quartic as mq


def _q(value):
    return Fraction(str(value))


def _canonical(values):
    vals = [_q(x) for x in values]
    den = 1
    for value in vals:
        den = den * value.denominator // gcd(den, value.denominator)
    ints = [int(value * den) for value in vals]
    common = reduce(gcd, (abs(x) for x in ints if x), 0)
    if common:
        ints = [x // common for x in ints]
    for value in ints:
        if value:
            if value < 0:
                ints = [-x for x in ints]
            break
    return tuple(ints)


def _right_compose(chart, source):
    e, f, g, h = source
    return _canonical((
        chart.A * e + chart.B * g,
        chart.A * f + chart.B * h,
        chart.C * e + chart.D * g,
        chart.C * f + chart.D * h,
    ))


def _arg_value(argv, flag, default=None):
    try:
        i = argv.index(flag)
    except ValueError:
        return default
    return argv[i + 1] if i + 1 < len(argv) else default


def _deduplicate(charts, *, protected_x, allow_inversion):
    """Quotient one ranked chart list by proved source-coordinate symmetries.

    Sign is always allowed.  Reciprocal actions are allowed only for rational
    source searches and only when the representative's source-infinity boundary
    maps to native infinity or to an already-protected native fibre.
    """
    charts = list(charts)
    protected = {_q(x) for x in (protected_x or [])}
    kept = []
    covered = {}
    skipped = []

    def record_orbit(chart, rep_index, rep_id, name, source):
        covered.setdefault(
            _right_compose(chart, source),
            {
                "representative_index": rep_index,
                "representative_chart_id": rep_id,
                "symmetry": name,
            },
        )

    for input_index, chart in enumerate(charts):
        sig = _canonical((chart.A, chart.B, chart.C, chart.D))
        prior = covered.get(sig)
        if prior is not None:
            skipped.append({"input_index": input_index, **prior})
            continue

        rep_index = len(kept)
        kept.append(chart)
        rep_id = str(getattr(chart, "chart_id", rep_index + 1))
        record_orbit(chart, rep_index, rep_id, "identity", (1, 0, 0, 1))
        record_orbit(chart, rep_index, rep_id, "negation", (-1, 0, 0, 1))

        # Inversion preserves projective rational height but exchanges affine
        # zero with source infinity.  Only quotient it when this boundary is
        # already accounted for by the chart's known/discovered anchor data.
        beta = getattr(chart, "beta", None)
        boundary_safe = beta is None or _q(beta) in protected
        if allow_inversion and boundary_safe:
            record_orbit(chart, rep_index, rep_id, "inversion", (0, 1, 1, 0))
            record_orbit(chart, rep_index, rep_id, "negative_inversion", (0, -1, 1, 0))

    return kept, skipped


def _refill(
    planner,
    call_args,
    call_kwargs,
    *,
    requested,
    protected_x,
    allow_inversion,
    audit,
    planner_name,
):
    """Return up to ``requested`` distinct representatives in ranking order."""
    requested = max(int(requested), 0)
    if requested <= 0:
        return []

    # Enough headroom for the ~45-50% duplicate rates observed in Campbell and
    # Mestre, while keeping planner work bounded.  Stop early if the planner
    # exhausts its candidate set before the requested limit.
    trial_limit = requested
    max_limit = max(requested * 4, requested + 64)
    last_raw_count = -1
    best_kept = []
    best_skipped = []

    while True:
        kw = dict(call_kwargs)
        kw["limit"] = trial_limit
        raw = list(planner(*call_args, **kw))
        kept, skipped = _deduplicate(
            raw,
            protected_x=protected_x,
            allow_inversion=allow_inversion,
        )
        best_kept, best_skipped = kept, skipped

        if len(kept) >= requested:
            best_kept = kept[:requested]
            break
        if len(raw) < trial_limit or len(raw) == last_raw_count or trial_limit >= max_limit:
            break
        last_raw_count = len(raw)
        trial_limit = min(max_limit, max(trial_limit * 2, trial_limit + requested))

    audit["planner_candidates_generated"] += max(0, len(best_kept) + len(best_skipped))
    audit["refill_extra_candidates"] += max(0, (len(best_kept) + len(best_skipped)) - requested)
    audit["refill_shortfall"] += max(0, requested - len(best_kept))
    audit["refill_plans"] += 1

    if best_skipped or trial_limit > requested:
        print(
            f"    [feature symmetry] {planner_name} refill-distinct requested={requested} "
            f"generated={len(best_kept)+len(best_skipped)} distinct={len(best_kept)} "
            f"duplicates={len(best_skipped)}",
            flush=True,
        )
    return best_kept


def main():
    ap = argparse.ArgumentParser(add_help=False)
    original = ap.add_mutually_exclusive_group(required=True)
    original.add_argument("--original-script")
    original.add_argument("--original-module")
    ap.add_argument("--family-kind", choices=["campbell", "mestre", "kihara"], required=True)
    ap.add_argument("--plan-mode", choices=["dedup", "refill"], default="dedup")
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    ns = ap.parse_args()

    rest = list(ns.rest)
    if rest and rest[0] == "--":
        rest = rest[1:]

    if ns.family_kind == "kihara":
        mode = "rational"
    else:
        mode = str(_arg_value(rest, "--mode", "both")).lower()

    allow_inversion = mode == "rational" and "--include-known-fibers" not in rest

    original_build = mq.build_chart_plan
    original_rank = mq.rank_charts

    audit = {
        "plans": 0,
        "input": 0,
        "retained": 0,
        "skipped": 0,
        "negation": 0,
        "inversion": 0,
        "refill_plans": 0,
        "planner_candidates_generated": 0,
        "refill_extra_candidates": 0,
        "refill_shortfall": 0,
    }

    def _audit_one(raw, kept, skipped, planner_name):
        audit["plans"] += 1
        audit["input"] += len(raw)
        audit["retained"] += len(kept)
        audit["skipped"] += len(skipped)
        audit["negation"] += sum(x["symmetry"] == "negation" for x in skipped)
        audit["inversion"] += sum(
            x["symmetry"] in {"inversion", "negative_inversion"} for x in skipped
        )
        if skipped:
            print(
                f"    [feature symmetry] {planner_name} exact source-height dedup "
                f"{len(raw)} -> {len(kept)} "
                f"({len(skipped)} skipped; "
                f"negation={sum(x['symmetry']=='negation' for x in skipped)} "
                f"inversion={sum(x['symmetry'] in {'inversion','negative_inversion'} for x in skipped)})",
                flush=True,
            )

    def reduced_build_chart_plan(coefficients, base_x, discovered_x=None, **kwargs):
        requested = int(kwargs.get("limit", 24))
        protected = set(base_x or ()) | set(discovered_x or ())
        if ns.plan_mode == "refill":
            # Refill mode intentionally expands the ranked candidate pool.
            kept = _refill(
                original_build,
                (coefficients, base_x, discovered_x),
                kwargs,
                requested=requested,
                protected_x=protected,
                allow_inversion=allow_inversion,
                audit=audit,
                planner_name="build_chart_plan",
            )
            # For high-level accounting, record requested -> launched.  Detailed
            # generated/duplicate counts live in the refill-specific fields.
            audit["plans"] += 1
            audit["input"] += requested
            audit["retained"] += len(kept)
            return kept

        raw = list(original_build(coefficients, base_x, discovered_x, **kwargs))
        kept, skipped = _deduplicate(raw, protected_x=protected, allow_inversion=allow_inversion)
        _audit_one(raw, kept, skipped, "build_chart_plan")
        return kept

    def reduced_rank_charts(coefficients, known_x, **kwargs):
        requested = int(kwargs.get("limit", 6))
        protected = set(known_x or ())
        if ns.plan_mode == "refill":
            kept = _refill(
                original_rank,
                (coefficients, known_x),
                kwargs,
                requested=requested,
                protected_x=protected,
                allow_inversion=allow_inversion,
                audit=audit,
                planner_name="rank_charts",
            )
            audit["plans"] += 1
            audit["input"] += requested
            audit["retained"] += len(kept)
            return kept

        raw = list(original_rank(coefficients, known_x, **kwargs))
        kept, skipped = _deduplicate(raw, protected_x=protected, allow_inversion=allow_inversion)
        _audit_one(raw, kept, skipped, "rank_charts")
        return kept

    # Patch both symbols.  Only the supported worker's imported symbol is used.
    mq.build_chart_plan = reduced_build_chart_plan
    mq.rank_charts = reduced_rank_charts

    if ns.original_script:
        script = Path(ns.original_script).resolve()
        sys.path.insert(0, str(script.parent))
        sys.argv = [str(script)] + rest
        runner = lambda: runpy.run_path(str(script), run_name="__main__")
    else:
        module = str(ns.original_module)
        sys.argv = [module] + rest
        runner = lambda: runpy.run_module(module, run_name="__main__", alter_sys=True)

    exit_code = 0
    try:
        runner()
    except SystemExit as exc:
        exit_code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 1
    finally:
        print(
            "RANK42_FEATURE_SYMMETRY_RESULT="
            + json.dumps(
                {
                    "status": "EXACT SOURCE-HEIGHT SYMMETRY COMPLETE",
                    "family_kind": ns.family_kind,
                    "plan_mode": ns.plan_mode,
                    "plans": audit["plans"],
                    "charts_planned": audit["input"],
                    "charts_searched_after_symmetry": audit["retained"],
                    "chart_symmetry_duplicates_skipped": audit["skipped"],
                    "negation_skipped": audit["negation"],
                    "inversion_skipped": audit["inversion"],
                    "inversion_enabled": allow_inversion,
                    "refill_plans": audit["refill_plans"],
                    "planner_candidates_generated": audit["planner_candidates_generated"],
                    "refill_extra_candidates": audit["refill_extra_candidates"],
                    "refill_shortfall": audit["refill_shortfall"],
                    "claim_boundary": (
                        "Exact source-coordinate search-space equivalence only; "
                        "refill mode changes coverage but never changes rank evidence by itself."
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
