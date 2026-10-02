#!/usr/bin/env python3
"""Exact Sage validation for every prescribed-torsion specialization."""
from __future__ import annotations

import json
from functools import reduce
from operator import mul
from pathlib import Path

from sage.all import QQ, EllipticCurve, sage_eval


ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "plugin.json").read_text())


def label(invariants):
    values = tuple(int(x) for x in invariants if int(x) > 1)
    if not values:
        return "Trivial"
    return " × ".join(f"C{x}" for x in values)


def main():
    checked = []
    for variant in MANIFEST["variants"]:
        path = ROOT / variant["family"]["file"]
        data = json.loads(path.read_text())
        parameter = str(data.get("parameter") or "t")
        t = QQ(str(variant["validation_parameter"]))
        ainvs = [
            QQ(sage_eval(str(expr), locals={parameter: t}))
            for expr in data["a_invariants"]
        ]
        E = EllipticCurve(QQ, ainvs)
        if E.discriminant() == 0:
            raise SystemExit(
                f"{variant['id']}: validation specialization is singular"
            )
        T = E.torsion_subgroup()
        invariants = tuple(int(x) for x in T.invariants() if int(x) > 1)
        exact = label(invariants)
        expected = str(variant["torsion_groups"][0])
        order = int(T.order())
        if order != reduce(mul, invariants, 1):
            raise SystemExit(
                f"{variant['id']}: torsion order/invariant mismatch"
            )
        if exact != expected:
            raise SystemExit(
                f"{variant['id']}: expected {expected}, got {exact} "
                f"at t={t} with invariants={invariants}"
            )
        checked.append((variant["id"], exact, order, str(t)))
        print(
            f"[ok] {variant['id']:<7} t={str(t):<8} "
            f"torsion={exact:<10} order={order}"
        )

    if len(checked) != 15:
        raise SystemExit(f"expected 15 variants, checked {len(checked)}")
    print(f"verified {len(checked)} exact torsion validation specializations")


if __name__ == "__main__":
    main()
