# Kihara (2001) · Rank ≥14 · v1.2.0

Rank Hunter Family plugin for Shoichi Kihara's elliptic curve over `Q(t)` of generic rank at least 14.

Release-audited for Rank Hunter **0.9.2**.

## Published source

Shoichi Kihara, *On an elliptic curve over Q(t) of rank ≥ 14*, Proc. Japan Acad. Ser. A Math. Sci. 77(4) (2001), 50–51.

- DOI: https://doi.org/10.3792/pjaa.77.50
- communicated: 12 April 2001
- published claim: `rank E(Q(t)) >= 14`

Kihara constructs a genus-one quartic from

```text
F(x) = product_{i=1}^{12} (x-b_i) = G(x)^2 - r(x),
deg r = 4,
```

with

```text
b_i     = u + a_i
b_{i+6} = -u + a_i
```

for six explicitly given `a_i(p,q)`, followed by the published one-parameter specialization `p(t),q(t),u(t)`.

The first twelve quartic points come from the twelve roots `b_i`; Kihara gives additional displayed abscissas for P13, P14 and P15. The elliptic group law uses P15 as origin.

## Kihara's rank-14 proof

Kihara proves the generic lower bound by specializing at

```text
t = 2.
```

For the specialized points `R1,...,R14` arising from `P1,...,P14`, the paper reports a nonzero determinant of the 14×14 canonical-height pairing matrix:

```text
221792776617402574.10
```

and concludes that the 14 specialized points are independent, hence the generic sections are independent.

## Rank Hunter reconstruction

The Family module reconstructs exactly:

- Kihara's `p(t), q(t), u(t)`;
- the twelve roots and genus-one quartic;
- P13 and P14 from the displayed abscissas by exact rational-square extraction;
- P15 as the quartic origin;
- the deterministic quartic-to-Weierstrass map;
- the fourteen generic sections P1..P14.

All quartic and elliptic maps used for scientific identity are exact.

## Generic-rank claim boundary

The release manifest declares:

```text
historical_generic_rank_lower = 14
verified_generic_rank_lower   = 14
generic_rank_claim_state      = generic_lower_bound_verified
```

Rank Hunter does **not** infer this operational certificate from paper metadata alone.

`validate_generic_rank_claim()` independently evaluates all fourteen exact sections at Kihara's own proof control `t=2` and runs Rank Hunter's exact independence certificate. If that exact certificate does not verify all fourteen directions, plugin validation fails.

This proves **generic rank at least 14**. Neither Kihara's paper nor this release claims exact generic rank 14.

For every ordinary specialization, Rank Hunter still exact-certifies the specialized baseline before writing a rigorous specialization lower bound.

## Search support

The Family supports:

- candidate generation;
- Family Search;
- Target Search;
- known-subgroup use;
- native quartic search;
- exact Möbius/PGL2 chart search;
- free search.

The discovery lane searches equivalent quartic charts, maps every hit exactly back to Kihara's native quartic, and then maps surviving points exactly to the specialized elliptic curve.

The fourteen known quartic fibers are recognized before expensive elliptic-curve work. Opposite-sign points on a known quartic fiber are handled through the exact involution relation rather than being misclassified as new rank directions.

Numerical canonical-height matrices/residuals are scheduling evidence only. They never promote rank.

## Specialization evidence

The plugin's `rank_claims.py` preserves the strict evidence contract:

- legacy unsupported `generic_lower` values are cleared;
- exact specialized sections are stored as rigorous witnesses only after a successful exact certificate;
- timeout/failure/inconclusive results do not write a lower bound;
- exact extra points are still candidates until subgroup independence is certified.

## Validation

Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout, then from the plugin repository run:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/kihara_rank14/tests
```

The release gate covers the exact family/quartic reconstruction, Kihara's `t=2` generic lower-bound certificate, current-core plugin/adapter validation, specialization-rank evidence behavior, and native/PGL2 interfaces.

A direct exact family sanity check is also available:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python families/kihara_rank14/doctor.py
```

## Version history

### v1.2.0

Rank Hunter 0.9.2 release audit. Adds an operational exact generic lower-bound-14 certificate at Kihara's published `t=2` proof control, refreshes source/claim provenance, removes stale local-install/path guidance, and adds current-core release validation.

### v1.1.1

Separated Kihara's historical generic-rank theorem from specialization evidence and required exact certification before storing specialization lower bounds.
