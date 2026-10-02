# Dujella–Peral · Z/4 · Rank 6

This Family reconstructs the Dujella–Peral elliptic curve over `Q(r)` with
torsion `Z/4Z` and exact generic rank 6.

The implementation uses the expanded model printed in the paper,

```text
y^2 = x^3 + a6(r)x^2 + b6(r)x,
```

together with the published full Mordell–Weil basis
`P1, P2, P3, P4, R5, R6`.

## Rank claim

Dujella and Peral prove exact rank 6 over `Q(r)`. Their construction first
produces six independent sections; they note that `r=1` is a valid
specialization for checking independence. They then verify the
Gusić–Tadić injectivity criterion at `r=13`, which proves the generic rank is
exactly 6.

Rank Hunter keeps those two statements separate:

- the manifest operationally exposes a **verified generic lower bound 6**;
- `validate_generic_rank_claim()` independently exact-certifies the six
  reconstructed sections at `r=1`;
- the paper's exact-rank-6 upper argument is retained as theorem provenance,
  because current core does not store a separate generic upper-bound evidence
  object.

## Torsion

The family has published torsion group `Z/4Z`. The factored `b6(r)` is a
square. The plugin reconstructs an explicit point halving `(0,0)` and checks
that it has exact order 4 on good specializations.

Rank Hunter validation also computes the exact torsion group on the manifest
control `r=1`; a torsion campaign still requires the exact specialized
torsion to equal `C4`.

## Search role

This is a high-generic-rank prescribed-`C4` subfamily, not the universal
`C4` parameter space. It therefore declares
`torsion_provider_role = prescribed_subfamily`.

The RELEASE package supports all three researcher-facing Family lanes:

- **Candidate generation** scores rational `r` specializations.
- **Family Search** reconstructs the published six-section basis on each stored
  specialization, then runs bounded completed-square ratpoints stages for exact
  extra points.
- **Target Search** deepens the same exact point search on one selected stored
  curve and can reconstruct the published basis if the point ledger is
  incomplete.

Both search paths are plugin-local and write no live scientific state. They emit
`rank42.plugin_geometry_result.v1` point artifacts into Rank Hunter's sandboxed
Pipeline boundary; core rechecks curve membership and owns exact independence
certification and every rank promotion.

## Source

Andrej Dujella and Juan Carlos Peral,
*An elliptic curve over Q(u) with torsion Z/4Z and rank 6*,
Rad Hrvatske akademije znanosti i umjetnosti. Matematičke znanosti 28 (2024),
185–192.

- DOI: `10.21857/y54jof4o2m`
- arXiv: `2207.08206`
