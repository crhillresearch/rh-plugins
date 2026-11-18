#!/usr/bin/env python3
"""Exact generic-torsion checks for the prescribed Mazur-family formulas.

For each family this verifies the marked subgroup over Q(t), then compares it
with the full rational torsion on one smooth specialization. Good reduction in
characteristic zero injects generic torsion into the specialized torsion, so
matching orders prove the full generic group.
"""
from __future__ import annotations

import hashlib
import json
from math import prod
from pathlib import Path

from sage.all import EllipticCurve, PolynomialRing, QQ, sage_eval


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "plugin.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text())
CERTIFICATE_PATH = ROOT / "generic_torsion_certificates.json"


def _label(invariants):
    values = tuple(int(value) for value in invariants if int(value) > 1)
    if not values:
        return "Trivial"
    return " × ".join(f"C{value}" for value in values)


def _prime_divisors(value):
    value = int(value)
    divisors = set()
    p = 2
    while p * p <= value:
        if value % p == 0:
            divisors.add(p)
            while value % p == 0:
                value //= p
        p += 1
    if value > 1:
        divisors.add(value)
    return sorted(divisors)


def _model_fingerprint(data):
    identity = {
        "parameter": str(data.get("parameter") or "u"),
        "a_invariants": [str(value) for value in data.get("a_invariants") or []],
        "function_field": "Q(u)",
    }
    return hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


def _exact_section(data, section, curve, parameter, parameter_name):
    x = sage_eval(str(section["x"]), locals={parameter_name: parameter})
    y = sage_eval(str(section["y"]), locals={parameter_name: parameter})
    point = curve(x, y)
    order = int(section["order"])
    if order <= 0 or order * point != curve(0):
        raise ValueError(f"{section.get('label')} is not killed by its declared order {order}")
    for prime in _prime_divisors(order):
        if (order // prime) * point == curve(0):
            raise ValueError(f"{section.get('label')} has order smaller than {order}")
    return point, order


def _verify_generic_subgroup(variant, data, generic_curve, parameter):
    group = str((variant.get("torsion_groups") or [""])[0])
    sections = data.get("sections") or []
    parameter_name = str(data.get("parameter") or "t")
    exact_points = [
        (section, *_exact_section(data, section, generic_curve, parameter, parameter_name))
        for section in sections if section.get("order") is not None
    ]

    if group == "Trivial":
        if exact_points:
            raise ValueError("the trivial-torsion source unexpectedly declares torsion sections")
        return {"method": "trivial_group"}, 1

    factors = [int(part[1:]) for part in group.split(" × ")]
    if len(factors) == 1:
        order = factors[0]
        witness = next((entry for entry in exact_points if entry[2] == order), None)
        if witness is None:
            raise ValueError(f"no exact order-{order} section for {group}")
        return {
            "group": group,
            "generator": witness[0].get("label"),
            "generator_order": order,
            "method": "exact_order_cyclic_generator",
        }, order

    if len(factors) != 2 or factors[0] != 2:
        raise ValueError(f"unsupported invariant factors for {group}")
    long_order = factors[1]
    long_generator = next((entry for entry in exact_points if entry[2] == long_order), None)
    if long_generator is None:
        raise ValueError(f"no exact order-{long_order} section for {group}")
    long_point = long_generator[1]
    order_two = next((entry for entry in exact_points
                      if entry[2] == 2 and entry[1] != (long_order // 2) * long_point), None)
    if order_two is None:
        raise ValueError(f"no independent order-two section for {group}")
    return {
        "group": group,
        "long_generator": long_generator[0].get("label"),
        "long_generator_order": long_order,
        "independent_order_two_section": order_two[0].get("label"),
        "method": "exact_invariant_factor_generators",
    }, 2 * long_order


def _verify_variant(variant):
    data = json.loads((ROOT / variant["family"]["file"]).read_text())
    parameter_name = str(data.get("parameter") or "t")
    rational_field = PolynomialRing(QQ, parameter_name).fraction_field()
    parameter = rational_field.gen()
    generic_ainvs = [sage_eval(str(expr), locals={parameter_name: parameter})
                     for expr in data["a_invariants"]]
    generic_curve = EllipticCurve(rational_field, generic_ainvs)
    if generic_curve.discriminant() == 0:
        raise ValueError("generic Weierstrass model is singular")
    subgroup, subgroup_order = _verify_generic_subgroup(
        variant, data, generic_curve, parameter,
    )

    specialization_parameter = QQ(str(variant["validation_parameter"]))
    specialized_ainvs = [QQ(sage_eval(
        str(expr), locals={parameter_name: specialization_parameter},
    )) for expr in data["a_invariants"]]
    specialized_curve = EllipticCurve(QQ, specialized_ainvs)
    if specialized_curve.discriminant() == 0:
        raise ValueError("validation specialization is singular")
    torsion = specialized_curve.torsion_subgroup()
    invariants = tuple(int(value) for value in torsion.invariants() if int(value) > 1)
    actual_group = _label(invariants)
    expected_group = str((variant.get("torsion_groups") or [""])[0])
    specialized_order = prod(invariants) if invariants else 1
    if actual_group != expected_group:
        raise ValueError(
            f"specialized torsion is {actual_group}, expected {expected_group}"
        )
    if specialized_order != subgroup_order:
        raise ValueError(
            f"generic subgroup order {subgroup_order} does not match full "
            f"specialized torsion order {specialized_order}"
        )

    certificate = {
        "schema": "rank42.generic_torsion_exact_certificate.v1",
        "method": "function_field_subgroup_and_good_fiber_torsion_injection",
        "family_model_sha256": _model_fingerprint(data),
        "group": expected_group,
        "function_field": "Q(t)",
        "function_field_subgroup": subgroup,
        "specialization": {
            "parameter": str(specialization_parameter),
            "torsion_invariants": list(invariants),
            "torsion_order": specialized_order,
            "discriminant_nonzero": True,
            "discriminant": str(specialized_curve.discriminant()),
            "exact_torsion_computed_over": "Q",
        },
        "specialization_torsion_injection": {
            "good_reduction": True,
            "residue_characteristic": 0,
            "statement": (
                "The generic marked subgroup has the same order as the full "
                "torsion group on this smooth rational fiber. Good reduction "
                "injects generic torsion into specialized torsion, so no larger "
                "generic torsion subgroup can occur."
            ),
        },
    }
    return certificate


def main():
    certificates = {}
    for variant in MANIFEST["variants"]:
        certificate = _verify_variant(variant)
        certificates[variant["id"]] = certificate
        print(
            f"[ok] {variant['id']:<7} {certificate['group']:<10} "
            f"t={certificate['specialization']['parameter']} · "
            f"exact generic torsion |G|={certificate['specialization']['torsion_order']}"
        )
    if len(certificates) != 15:
        raise SystemExit(f"expected 15 variants, verified {len(certificates)}")
    CERTIFICATE_PATH.write_text(
        json.dumps(certificates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"verified {len(certificates)} exact generic torsion groups")
    print(f"certificate file: {CERTIFICATE_PATH}")


if __name__ == "__main__":
    main()
