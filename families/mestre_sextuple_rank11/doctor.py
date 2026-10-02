"""Standalone exact sanity check for the Mestre sextuple plugin."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sage.all import QQ
import family


def main():
    symbolic = family.validate_symbolically()
    check = family.construction_check(QQ(1))
    if not symbolic.get("identity_verified"):
        raise SystemExit("Mestre symbolic identity check failed")
    if check["base_fibres"] != 12 or check["sections"] != 11:
        raise SystemExit("Mestre section/base-fibre check failed")
    if not check["t_sign_quartic_symmetry"]:
        raise SystemExit("Mestre t <-> -t quartic symmetry check failed")
    print(json.dumps({
        "status": "ok",
        "family": family.name(),
        "symbolic_identity": True,
        "base_fibres": 12,
        "sections": 11,
        "t_sign_quartic_symmetry": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
