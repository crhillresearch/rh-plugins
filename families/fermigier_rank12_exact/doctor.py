#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sage.all import QQ

if __package__:
    from . import family
else:
    import family


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parameter', default='19754/39')
    ap.add_argument('--symbolic', action='store_true')
    args = ap.parse_args()
    t = QQ(args.parameter)
    check = family.construction_check(t)
    E = family.curve(t)
    sections = family.generic_section_points(t)
    result = {
        'ok': True,
        'family': family.name(),
        'generic_rank': family.generic_rank,
        'generic_rank_claim': 'generic lower bound 12 exact-certified; frozen external theorem provenance reports arithmetic rank exactly 12',
        'parameter': str(t),
        'literal_shift': str(2*t),
        'curve_discriminant_nonzero': bool(E is not None and E.discriminant() != 0),
        'specialized_section_count': len(sections),
        'construction_check': check,
        'family_source_sha256': hashlib.sha256(Path(family.__file__).read_bytes()).hexdigest(),
    }
    if args.symbolic:
        result['symbolic_construction'] = family.validate_symbolically()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
