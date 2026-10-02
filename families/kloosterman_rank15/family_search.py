#!/usr/bin/env python3
"""Compatibility launcher for Kloosterman Family Search.

v1.1.0 delegates the actual screening to Rank Hunter's current auto_analyze
pipeline so rigorous quick bounds are recorded in the core rank-evidence ledger.
The file remains for users/scripts that invoked the old plugin runner directly.
"""
from __future__ import annotations

import argparse
import os
import sys


def parse_args():
    ap = argparse.ArgumentParser(description="Kloosterman rank-15 Family Search compatibility launcher")
    ap.add_argument("--input", required=True)
    ap.add_argument("--family", required=True)
    ap.add_argument("--db", default="rank42.db")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--primary-strategy", choices=["pari", "mwrank"], default="pari")
    ap.add_argument("--quick-timeout", type=int, default=120)
    return ap.parse_args()


def main():
    args = parse_args()
    cmd = [
        sys.executable, "-m", "rank42.auto_analyze",
        "--db", str(args.db),
        "--input", str(args.input),
        "--family", str(args.family),
        "--limit", str(int(args.limit)),
        "--quick-strategy", str(args.primary_strategy),
        "--quick-timeout", str(int(args.quick_timeout)),
        "--fast-screen",
        "--quick-only",
        "--no-generic-witness",
    ]
    os.execv(sys.executable, cmd)


if __name__ == "__main__":
    main()
