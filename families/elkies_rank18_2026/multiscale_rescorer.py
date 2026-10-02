#!/usr/bin/env python3
"""Second-stage multiscale Nagao rescorer for Elkies's rank-18 cover.

This is a search-priority tool only.  It reads stage-one candidate JSONL,
recomputes the finite-prime Nagao-style sum at larger prime cutoffs, and ranks
by persistence/growth.  It never creates rank evidence and never runs descent.

The intended funnel is:
    broad rational-r scan -> multiscale rescore -> raw point search ->
    exact independence certificate only if an extra point is found.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

from sage.all import QQ

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import rank18_family as family

DB_FAMILY_NAME = "Elkies 2026 first rank-18 quadratic cover over Q(r)"


def _find_project_root():
    starts = (Path.cwd().resolve(), HERE)
    seen = set()
    for start in starts:
        for candidate in (start, *start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / "rank42").is_dir():
                return candidate
    return Path.cwd().resolve()


def parse_bounds(text):
    bounds = sorted({int(x.strip()) for x in str(text).split(",") if x.strip()})
    if not bounds or bounds[0] < 5:
        raise ValueError("bounds must contain integers >= 5")
    return bounds


def primes_upto(n):
    n = int(n)
    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, int(n ** 0.5) + 1):
        if sieve[p]:
            start = p * p
            sieve[start:n + 1:p] = b"\x00" * (((n - start) // p) + 1)
    return [p for p in range(3, n + 1) if sieve[p]]


def parameter_of(row):
    for key in ("r", "parameter", "s", "t"):
        if row.get(key) is not None:
            return Fraction(str(row[key]))
    if row.get("a") is not None and row.get("b") is not None:
        return Fraction(int(row["a"]), int(row["b"]))
    raise ValueError("candidate row has no rational parameter")


def load_rows(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: float(r.get("score") or 0.0), reverse=True)
    return rows


def exclude_known_rows(rows, db_path):
    root = _find_project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from rank42.db import connect, get_curve_by_key

    db = connect(db_path)
    unseen = []
    skipped = 0
    try:
        for row in rows:
            r = str(parameter_of(row))
            if get_curve_by_key(db, DB_FAMILY_NAME, r) is None:
                unseen.append(row)
            else:
                skipped += 1
    finally:
        db.close()
    return unseen, skipped


def _snapshot(cumulative, good, denominator_bad, singular_bad,
              prime_window, good_weight, total_weight):
    return {
        "score": cumulative,
        "good_primes": good,
        "denominator_bad_primes": denominator_bad,
        "singular_bad_primes": singular_bad,
        "prime_window": prime_window,
        "good_prime_fraction": (float(good) / prime_window) if prime_window else 0.0,
        "good_weight_fraction": (good_weight / total_weight) if total_weight else 0.0,
    }


def score_at_bounds(r_text, bounds, primes):
    f = Fraction(str(r_text))
    rq = QQ(f.numerator) / QQ(f.denominator)
    E = family.curve(rq)
    if E is None:
        raise ValueError(f"singular/undefined specialization r={f}")

    ainvs = list(E.a_invariants())
    disc = QQ(E.discriminant())

    snapshots = {}
    cumulative = 0.0
    good = 0
    denominator_bad = 0
    singular_bad = 0
    prime_window = 0
    good_weight = 0.0
    total_weight = 0.0
    bi = 0

    for p in primes:
        while bi < len(bounds) and p > bounds[bi]:
            snapshots[bounds[bi]] = _snapshot(
                cumulative, good, denominator_bad, singular_bad,
                prime_window, good_weight, total_weight,
            )
            bi += 1

        weight = math.log(p) / p
        prime_window += 1
        total_weight += weight

        # Conservative model-local bad-prime handling.  Skipping a prime whose
        # displayed rational model has a denominator is safe for this heuristic
        # and is tracked explicitly so coverage differences remain visible.
        if any(int(QQ(a).denominator()) % p == 0 for a in ainvs) or int(disc.denominator()) % p == 0:
            denominator_bad += 1
            continue
        if int(disc.numerator()) % p == 0:
            singular_bad += 1
            continue

        try:
            cumulative += (-int(E.ap(p))) * weight
        except (ArithmeticError, ValueError, ZeroDivisionError):
            singular_bad += 1
            continue
        good += 1
        good_weight += weight

    while bi < len(bounds):
        snapshots[bounds[bi]] = _snapshot(
            cumulative, good, denominator_bad, singular_bad,
            prime_window, good_weight, total_weight,
        )
        bi += 1

    return snapshots


def parse_args():
    ap = argparse.ArgumentParser(description="Multiscale Nagao rescorer for Elkies rank-18 specializations")
    ap.add_argument("--input", required=True, help="stage-one candidate JSONL")
    ap.add_argument("--output", default="/tmp/elkies_rank18_multiscale.jsonl")
    ap.add_argument("--limit", type=int, default=1000, help="rescore the top N eligible stage-one candidates")
    ap.add_argument("--bounds", default="251,503,1009,2003")
    ap.add_argument("--progress-every", type=int, default=25)
    ap.add_argument("--db", default="rank42.db", help="Rank Hunter DB used with --exclude-known")
    ap.add_argument("--exclude-known", action="store_true", help="skip rank-18 fibers already present in the DB")
    return ap.parse_args()


def main():
    args = parse_args()
    bounds = parse_bounds(args.bounds)
    rows = load_rows(args.input)
    skipped = 0
    if args.exclude_known:
        rows, skipped = exclude_known_rows(rows, args.db)
    rows = rows[: int(args.limit)]
    primes = primes_upto(max(bounds))

    print("RANK HUNTER · ELKIES RANK-18 MULTISCALE RESCORER", flush=True)
    print("=" * 72, flush=True)
    if args.exclude_known:
        print(f"[known] skipped {skipped} fibers already present in {args.db}", flush=True)
    print(f"[input] {len(rows)} eligible stage-one candidates", flush=True)
    print(f"[bounds] {','.join(str(b) for b in bounds)}", flush=True)
    print("[scientific status] heuristic priority only; no rank claim", flush=True)
    print("[next stage] raw rational-point search; descent is deliberately not in this funnel", flush=True)

    out = []
    first = bounds[0]
    last = bounds[-1]

    for i, row in enumerate(rows, 1):
        r = parameter_of(row)
        try:
            snap = score_at_bounds(r, bounds, primes)
        except ValueError as exc:
            print(f"[rescore] {i}/{len(rows)} r={r} skipped: {exc}", flush=True)
            continue

        enriched = dict(row)
        enriched["r"] = str(r)
        enriched["stage1_score"] = float(row.get("score") or 0.0)
        enriched["multiscale_bounds"] = bounds
        enriched["score_kind"] = "elkies_rank18_nagao_multiscale_v1"

        for bound in bounds:
            info = snap[bound]
            enriched[f"nagao_{bound}"] = info["score"]
            enriched[f"good_primes_{bound}"] = info["good_primes"]
            enriched[f"denominator_bad_primes_{bound}"] = info["denominator_bad_primes"]
            enriched[f"singular_bad_primes_{bound}"] = info["singular_bad_primes"]
            enriched[f"prime_window_{bound}"] = info["prime_window"]
            enriched[f"good_prime_fraction_{bound}"] = info["good_prime_fraction"]
            enriched[f"good_weight_fraction_{bound}"] = info["good_weight_fraction"]

        enriched["multiscale_growth"] = enriched[f"nagao_{last}"] - enriched[f"nagao_{first}"]
        enriched["multiscale_terminal"] = enriched[f"nagao_{last}"]
        enriched["multiscale_floor"] = min(enriched[f"nagao_{b}"] for b in bounds)
        out.append(enriched)

        if args.progress_every > 0 and i % args.progress_every == 0:
            print(f"[rescore] {i}/{len(rows)}", flush=True)

    # Match the empirically useful Three Lanterns policy: growth/persistence is
    # primary, terminal score and the original stage-one score break ties.
    out.sort(
        key=lambda r: (
            float(r["multiscale_growth"]),
            float(r["multiscale_terminal"]),
            float(r.get("stage1_score") or 0.0),
        ),
        reverse=True,
    )

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in out:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    print()
    print(f"[output] {len(out)} rescored candidates -> {path}", flush=True)
    print("TOP MULTISCALE CANDIDATES", flush=True)
    for row in out[:20]:
        print(
            f"r={row['r']:>18}  "
            f"N{first}={row[f'nagao_{first}']:7.3f}  "
            f"N{last}={row[f'nagao_{last}']:7.3f}  "
            f"growth={row['multiscale_growth']:7.3f}  "
            f"coverage={row[f'good_prime_fraction_{last}']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
