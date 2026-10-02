# Kihara (2001) provenance and claim ledger

## Primary source

Shoichi Kihara, *On an elliptic curve over Q(t) of rank >= 14*,
Proc. Japan Acad. Ser. A Math. Sci. 77(4) (2001), 50–51.

DOI: `10.3792/pjaa.77.50`.

The paper states and proves that the resulting elliptic curve over `Q(t)`
has Mordell–Weil rank at least 14.

## Published construction

Kihara starts from

```text
F(x)=product_{i=1}^{12}(x-b_i)=G(x)^2-r(x),
deg r = 4,
```

with
`b_i=u+a_i` and `b_{i+6}=-u+a_i` for six explicit `a_i(p,q)`.
He then gives the one-parameter specialization `p(t),q(t),u(t)`.

The twelve roots give twelve rational quartic points. Kihara also displays
additional abscissas for P13, P14 and P15, and uses P15 as the elliptic origin.

## Published independence proof

Kihara specializes at `t=2`.

For the specialized images `R1,...,R14` of `P1,...,P14`, the paper reports
the canonical-height Gram determinant

```text
221792776617402574.10
```

as nonzero and concludes that the fourteen specialized points are independent.
Therefore the fourteen generic sections are independent over `Q(t)`.

This is a rank-**at-least**-14 theorem. The paper does not claim exact generic
rank 14.

## Rank Hunter reconstruction

The plugin reconstructs exactly:

- the published `p,q,u` specialization;
- the six shifts and twelve roots;
- the quartic remainder `r(x)`;
- P13 and P14 from Kihara's displayed x-coordinates by exact square-root extraction;
- P15 and the exact quartic-to-Weierstrass transformation;
- the fourteen sections P1..P14.

The finite-field screen uses the classical binary-quartic Jacobian invariants;
the rational scientific model uses the exact P15-origin map.

## Operational 0.9.2 certificate

The RELEASE manifest records

```text
historical_generic_rank_lower = 14
verified_generic_rank_lower = 14
generic_rank_claim_state = generic_lower_bound_verified
```

The operational certificate is not synthesized from the paper's numerical
height determinant.

`validate_generic_rank_claim()` independently specializes the reconstructed
fourteen sections at `t=2` and invokes Rank Hunter's exact lower-bound
certificate. Plugin activation succeeds only when that exact certificate proves
all fourteen directions independent.

The mathematical implication is the same specialization argument used by
Kihara: a generic integral relation would remain a relation at a good
specialization, so exact independence at `t=2` proves generic independence.

## Specialization claim boundary

Generic information never assigns a rank to an arbitrary rational fiber.

For each specialization:
- the fourteen sections are mapped exactly;
- a rigorous specialization lower bound is written only after exact independence certification;
- timeout/failure/inconclusive certificate results write no lower bound;
- exact additional points are candidate evidence until their independence is certified;
- numerical canonical-height screens are scheduling evidence only.

## Search-map boundary

Native quartic points, Möbius/PGL2 transformations, inverse chart maps, and
quartic-to-elliptic maps are exact.

The hyperelliptic involution on the native quartic is handled through the exact
elliptic relation `P -> T-P`, so the opposite sign of a known quartic fiber is
not automatically treated as a new independent point.
