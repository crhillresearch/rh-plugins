"""Standalone exact sanity check for the Kihara plugin."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sage.all import QQ
import family


def main():
    check = family.construction_check(QQ(2))
    known = family.native_quartic_known_points(QQ(2))
    coeffs = family.quartic_search_coefficients(QQ(2))
    if check["sections"] != 14 or check["distinct_nonzero"] != 14:
        raise SystemExit("Kihara section check failed")
    if len(known) != 14 or len(coeffs) != 5:
        raise SystemExit("Kihara quartic interface check failed")
    print(json.dumps({
        "status": "ok",
        "family": family.name(),
        "parameter": "2",
        "sections": 14,
        "native_known_points": 14,
        "quartic_coefficients": 5,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
