# Dujella–Peral Z/4 rank-6 provenance

## Primary source

A. Dujella and J. C. Peral,
*An elliptic curve over Q(u) with torsion Z/4Z and rank 6*,
Rad Hrvatske akademije znanosti i umjetnosti. Matematičke znanosti 28 (2024),
185–192.

DOI: `10.21857/y54jof4o2m`.
Preprint: arXiv `2207.08206v2`.

## Published construction

The paper starts from Elkies's rank-4 `Z/4Z` K3 surface and imposes two
quadratic-section conditions simultaneously. The resulting rational base
change is

```text
t =
4(3r^2 - 14r - 5390)(10r^2 - 14r - 1617)
------------------------------------------------
7(72r^4 - 182r^3 - 13279r^2 + 98098r + 20917512).
```

After clearing denominators the paper prints

```text
y^2 = x^3 + a6(r)x^2 + b6(r)x,
```

with expanded `a6` and factored square `b6`. The plugin transcribes those
coefficients exactly.

The paper prints six independent points `P1,...,P6`, then observes that their
subgroup has index 4 modulo torsion. It gives points `R5,R6` satisfying
halving relations and states that

```text
P1, P2, P3, P4, R5, R6
```

generate the full Mordell–Weil group modulo torsion. Rank Hunter uses this
published full basis.

## Generic rank

The paper gives two distinct controls:

1. `r=1`: the six displayed points specialize to six independent rational
   points, proving generic rank at least 6.
2. `r=13`: the Gusić–Tadić injectivity conditions are satisfied, and the
   paper concludes the rank over `Q(r)` is exactly 6.

Rank Hunter independently reconstructs only the lower-bound part as
operational evidence. `validate_generic_rank_claim()` exact-certifies the six
published basis directions at `r=1`.

The exact generic-rank-6 theorem is preserved in manifest provenance; it is not
silently converted into a Rank Hunter generic upper-bound object.

## Torsion boundary

The paper's family has torsion `Z/4Z`. The plugin reconstructs an explicit
order-4 point from the square factor of `b6` and current-core validation
computes exact specialized torsion at `r=1`.

A generic family label never substitutes for exact torsion computation on a
candidate specialization.

## Heuristic boundary

Nagao scoring and candidate ordering are search heuristics only. A specialized
rank lower bound rises only from exact rational points with an exact
independence certificate.

## Search adapter boundary

The release adapter does not use the historical database-wide incumbent pruning
path. That would be inappropriate for a prescribed-C4 record lane because a
high-rank curve in another torsion class is not the relevant C4 incumbent.

Family Search and Target Search instead run a plugin-local exact point finder.
It reconstructs the published six-section basis, optionally moves the stored
curve to a bounded exact minimal model for ratpoints, maps every hit back
exactly, and emits only point candidates through
`rank42.plugin_geometry_result.v1`.

The plugin runner performs no live scientific writes and makes no independence
claim. Rank Hunter core validates the returned points and owns all exact
certification/rank promotion.
