"""Family-aware Target bridge for one stored Fibonacci-family specialization.

Rank Hunter's generic ``auto_analyze`` worker accepts a candidate JSONL file,
while the Target UI identifies a stored curve by id.  This worker translates
only that orchestration boundary: it recovers the exact rational family
parameter, validates that the selected family matches the stored curve, writes
one temporary candidate record, and runs core ``auto_analyze`` with the known
family sections still enabled.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from fractions import Fraction


def candidate_record(parameter, score=None):
    """Return the one-row exact candidate representation expected by auto_analyze."""
    t = Fraction(str(parameter))
    return {
        "a": int(t.numerator),
        "b": int(t.denominator),
        "score": float(score) if score is not None else 0.0,
    }


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Family-aware target re-screen for Fibonacci Triple Curves")
    ap.add_argument("--db", default="rank42.db")
    ap.add_argument("--curve-id", type=int, required=True)
    ap.add_argument("--family", required=True)
    ap.add_argument("--quick-timeout", type=int, default=120)
    ap.add_argument("--quick-strategy", choices=("pari", "mwrank"), default="pari")
    ap.add_argument("--strong-timeout", type=int, default=600)
    ap.add_argument("--generic-certificate-timeout", type=int, default=120)
    ap.add_argument("--quick-only", action="store_true")
    ap.add_argument("--fast-screen", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Import Rank Hunter only in the science worker so this module's exact
    # parameter translation remains unit-testable without Sage installed.
    from rank42.db import connect, get_curve
    from rank42.family_loader import load_family, resolve_family_spec

    db = connect(args.db)
    try:
        row = get_curve(db, args.curve_id)
        if row is None:
            raise SystemExit(f"curve #{args.curve_id} not found")
        if not row["parameter"]:
            raise SystemExit(f"curve #{args.curve_id} has no stored family parameter")
        parameter = str(row["parameter"])
        score = row["score"]
        stored_family = str(row["family"] or "")
    finally:
        db.close()

    family_spec = resolve_family_spec(args.family)
    family = load_family(family_spec, need_sections=True)
    if stored_family != str(family.name()):
        raise SystemExit(
            f"curve #{args.curve_id} belongs to {stored_family!r}, "
            f"but target adapter resolved {family.name()!r}"
        )

    record = candidate_record(parameter, score)
    fd, candidate_path = tempfile.mkstemp(prefix=f"rank42-target-{args.curve_id}-", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

        auto_args = [
            "--db", str(args.db),
            "--input", candidate_path,
            "--family", str(family_spec),
            "--limit", "1",
            "--force",
            "--quick-timeout", str(int(args.quick_timeout)),
            "--quick-strategy", str(args.quick_strategy),
            "--strong-timeout", str(int(args.strong_timeout)),
            "--generic-certificate-timeout", str(int(args.generic_certificate_timeout)),
        ]
        if args.quick_only:
            auto_args.append("--quick-only")
        if args.fast_screen:
            auto_args.append("--fast-screen")

        from rank42 import auto_analyze

        old_argv = sys.argv
        try:
            sys.argv = ["rank42.auto_analyze", *auto_args]
            return auto_analyze.main()
        finally:
            sys.argv = old_argv
    finally:
        try:
            os.unlink(candidate_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
