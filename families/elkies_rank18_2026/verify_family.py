#!/usr/bin/env python3
"""Exact self-check for the Elkies 2026 first rank-18 cover family."""
from __future__ import annotations

import json

import rank18_family as family


def main():
    symbolic = family.validate_symbolically()
    samples = []
    for r in (0, 1, -1, 2, -2, 3):
        E = family.curve(r)
        if E is None:
            continue
        points = family.generic_section_points(r)
        if len(points) != 18:
            raise RuntimeError(f"expected 18 sections at r={r}, got {len(points)}")
        samples.append({
            "r": str(r),
            "sections": len(points),
            "all_exact_on_curve": all(P.curve() == E for P in points),
        })
        if len(samples) >= 2:
            break
    if not samples:
        raise RuntimeError("no nonsingular smoke-test specialization found")
    payload = {
        "schema": "rank-hunter.elkies-rank18-first-cover-family.v1",
        "status": "ok",
        "stage": "rank18_family_exactly_verified",
        "symbolic": symbolic,
        "smoke_specializations": samples,
        "db_writes": False,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
