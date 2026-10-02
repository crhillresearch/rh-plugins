# Dujella–Peral–Tadić · Z/6 · Rank 3 Families

One Rank Hunter Family plugin containing the explicit one-parameter
`Z/6Z`, generic-rank-3 families analyzed in Dujella–Peral–Tadić (2016).

## Variants

| Variant | Paper | Injective control | Basis used by Rank Hunter |
| --- | --- | ---: | --- |
| Lecacheux | §3 | `t=-7` | `P1,P2,P3` |
| Kihara | §4 | `t=15` | corrected full basis `W1,W2,Q3` |
| Eroshkin `v=+1/3` | §5 | `t=-11` | `R1,R2,R3` |
| Eroshkin `v=-1/3` | §5 | `t=-15` | `S1,S2,S3` |
| Dujella–Peral direct | §6 | `t=13` | `P1,P2,P3` |
| MacLeod | §7 | `t=-30` | `Q1,Q2,Q3` |

Kihara is the default UI variant because the paper reports the broadest set of
rank-8 specializations from that branch. Eroshkin's two rank-3 specializations
are separate variants because they have different coefficient models, bases,
injective controls, and observed high-rank behavior.

Woo is **not** included: the paper mentions Woo historically but does not print
a reconstruction-grade explicit one-parameter model and free basis for a
release variant.

## Exact rank boundary

The paper applies the Gusić–Tadić specialization criterion to each included
family, proves generic rank exactly 3, and determines free generators.

Rank Hunter keeps theorem provenance separate from operational evidence:
each variant's `validate_generic_rank_claim()` exact-certifies the printed
three-generator basis at the paper's injective control. Candidate
specializations receive rank credit only through exact point membership and
core-owned exact independence certification.

## Search

Every variant supports:

- Candidate Generation in its own rational parameter `t`;
- Family Search using its printed rank-3 basis plus staged completed-square
  ratpoints;
- Target Search on one stored specialization, preserving the originating
  variant and reconstructing the printed basis when useful.

The search runner is write-free. It emits
`rank42.plugin_geometry_result.v1`; Rank Hunter core validates points and owns
all live scientific state and rank promotion.

## Source

Andrej Dujella, Juan Carlos Peral, Petra Tadić,
*Elliptic curves with torsion group Z/6Z*,
Glasnik Matematički 51(2) (2016), 321–333.

- DOI: `10.3336/gm.51.2.03`
- arXiv: `1503.03667`
