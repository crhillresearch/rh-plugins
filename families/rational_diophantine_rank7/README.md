# Dujella–Peral · Rational Diophantine Triple Rank ≥7

This plugin implements the explicit infinite rank-`>=7` construction from
§3 of Dujella–Peral (2020).

This Family is deliberately different from an ordinary one-parameter
`Q(t)` Family. The seventh section exists on the genus-1 base

```text
z^2 = 54 w3^4 + 2736 w3^3 + 66592 w3^2 + 2987712 w3 + 64393056.
```

The paper proves this quartic is birational to a rank-3 elliptic curve, hence it
has infinitely many rational points. For rational base points, conditions (8)
or (9) relate the second and third rank-6 constructions; the six points on curve
(12) together with the transported sixth point from curve (11) give seven
independent sections.

## Exact parameter semantics

Rank Hunter uses `w3` as the visible parameter, but **accepts it only when the
quartic value is an exact rational square**. It then reconstructs the
corresponding `w2` from condition (8).

At the paper control:

```text
w3 = 26
z  = 16120
w2 = -76/3
```

the plugin reproduces the exact curve and all seven x-coordinates printed in
the paper.

Candidate Generation applies the same quartic-square condition modulo each good
prime. This makes Nagao scoring also act as a local-solubility sieve. Exact
`curve(w3)` construction remains the hard rational gate; locally soluble but
globally invalid candidates receive no rank-7 curve.

## Rank claim

The paper proves an **infinite family with rank at least 7**. It does not prove
that the generic rank over the genus-1 base is exactly 7.

Rank Hunter therefore exposes only a verified operational lower bound 7.
`validate_generic_rank_claim()` exact-certifies the seven sections at the
paper's control `(w2,w3)=(-76/3,26)`.

## Search

Candidate Generation, Family Search and Target Search are all supported.
Family/Target Search reconstructs all seven exact sections and then performs
bounded completed-square ratpoints stages for extras. The plugin runner is
write-free; core validates and certifies every returned point.

## Second infinite rank-7 construction

The paper also derives another infinite rank-`>=7` family by intersecting the
second and fifth rank-6 substitutions. It prints the base equations and an
independence control but not the explicit transported seventh-section formula
needed for Rank Hunter's release proof boundary. It is preserved in provenance,
not synthesized as a second variant.

## Source

Andrej Dujella and Juan Carlos Peral,
*High rank elliptic curves induced by rational Diophantine triples*,
Glasnik Matematički 55(2) (2020), 237–252,
DOI `10.3336/gm.55.2.05`, arXiv `2005.10706`.
