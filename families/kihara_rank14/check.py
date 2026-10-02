import argparse
import json
from pathlib import Path

from sage.all import QQ

# Plugin workers are executed by absolute path.  When Rank Hunter is run from
# a source checkout, keep the core checkout importable without requiring the
# plugin itself to live inside that checkout.
import sys
_CORE_CWD = Path.cwd().resolve()
if (_CORE_CWD / "rank42").is_dir() and str(_CORE_CWD) not in sys.path:
    sys.path.insert(0, str(_CORE_CWD))

import family
from rank42.mathutil import height_screen


def parse_args():
    ap = argparse.ArgumentParser(description="Validate the Kihara 2001 rank-14 construction.")
    ap.add_argument("--t", default="2")
    ap.add_argument("--height", action="store_true", help="also compute the canonical-height matrix")
    ap.add_argument("--precision", type=int, default=192)
    return ap.parse_args()


def main():
    args = parse_args()
    t = QQ(args.t)
    result = family.construction_check(t)
    print("RANK HUNTER KIHARA 2001 CHECK")
    print("=" * 62)
    print("family              =", result["family"])
    print("parameter           =", result["parameter"])
    print("sections            =", result["sections"])
    print("distinct nonzero    =", result["distinct_nonzero"])
    print("a-invariants        =", result["a_invariants"])

    if args.height:
        E = family.curve(t)
        pts = family.generic_section_points(t)
        print(f"[height] computing {len(pts)}x{len(pts)} matrix at {args.precision} bits...")
        info = height_screen(E, pts, precision=args.precision)
        print("height positive     =", info.get("positive_definite_screen"))
        print("height determinant  =", info.get("determinant"))
        print("min eigenvalue      =", info.get("min_eigenvalue"))
        if t == 2:
            print("paper determinant   ~ 2.2179277661740257410e17")


if __name__ == "__main__":
    main()
