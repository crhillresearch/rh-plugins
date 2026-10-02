# Provenance — Dujella–Peral–Tadić Z/6 rank-3 families

Primary source: A. Dujella, J. C. Peral, P. Tadić,
*Elliptic curves with torsion group Z/6Z*, Glasnik Matematički 51(2) (2016),
321–333, DOI `10.3336/gm.51.2.03`, arXiv `1503.03667`.

The plugin transcribes the six explicit one-parameter rank-3 models for which
the paper prints enough data to reconstruct the curve, three free generators,
and an injective specialization control:

- Lecacheux (§3), control `t=-7`;
- Kihara (§4), control `t=15`;
- Eroshkin `v=+1/3` (§5), control `t=-11`;
- Eroshkin `v=-1/3` (§5), control `t=-15`;
- Dujella–Peral direct (§6), control `t=13`;
- MacLeod (§7), control `t=-30`.

For Kihara, the paper explicitly shows that Kihara's original
`Q1,Q2,Q3` do not form a full free basis and replaces them by
`W1,W2,Q3`. Rank Hunter uses that corrected basis.

For Eroshkin, both signs `v=±1/3` are retained because the paper proves
exact rank 3 for both and supplies different explicit coefficient/basis data.

The paper mentions Woo historically but does not present a complete explicit
one-parameter model/basis in its detailed sections; no Woo variant is inferred
or synthesized here.

## Proof boundary

The paper's Gusić–Tadić arguments prove exact generic rank 3. Rank Hunter
operationally reconstructs only the lower-bound side: the printed free basis is
specialized at the paper's injective control and passed through Rank Hunter's
exact independence certificate.

The manifest's exact-rank statements remain theorem provenance. Specialized
candidate rank and torsion are computed independently by Rank Hunter.

## Search boundary

The common Family/Target runner is variant-aware and write-free. It reconstructs
the selected variant's printed basis, optionally searches a bounded exact
minimal model with ratpoints, maps hits back exactly, and emits only typed point
artifacts. Core owns live persistence and proof promotion.
