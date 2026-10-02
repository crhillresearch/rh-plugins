#!/usr/bin/env python3
"""Exact self-check for the Elkies 2026 plugin. Run with the Sage environment."""
from __future__ import annotations
import json, sys
from pathlib import Path

def _find_project_root():
    """Find the active Rank Hunter root without assuming plugin nesting depth."""
    starts = (Path.cwd().resolve(), Path(__file__).resolve().parent)
    seen = set()
    for start in starts:
        for candidate in (start, *start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / "rank42").is_dir():
                return candidate
    return Path.cwd().resolve()


PROJECT_ROOT = _find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.all import QQ, PolynomialRing, matrix
from rank42.formula_family import FormulaFamily

HERE = Path(__file__).resolve().parent
family = FormulaFamily.from_json(HERE / "family.json")
print(json.dumps(family.validate_symbolically(), indent=2, sort_keys=True))

R = PolynomialRing(QQ, "t")
t = R.gen()
data = json.loads((HERE / "family.json").read_text())
# Evaluate through the FormulaFamily parser to keep this check aligned with production loading.
K = R.fraction_field(); tk = K(t)
xs=[]; ys=[]
for rec in data["sections"]:
    xs.append(R(K(family._eval(rec["x"], tk))))
    ys.append(R(K(family._eval(rec["y"], tk))))

def pairing(i,j):
    if i == j: return 4
    dx=xs[i]-xs[j]; dy=ys[i]-ys[j]
    g=dx.gcd(dy)
    finite=g.degree()
    infinity=min(4-dx.degree(),6-dy.degree())
    return 2-(finite+infinity)

G=matrix(QQ,17,17,lambda i,j: pairing(i,j))
expected=json.loads((HERE/'data'/'published_height_gram.json').read_text())['gram_matrix']
assert [[int(G[i,j]) for j in range(17)] for i in range(17)] == expected
assert G.det() == 948
print("published height Gram: MATCH")
print("determinant:", G.det())
print("sections:", len(xs))
