# Z/2 × Z/6 Rank-2 Families · Dujella–Kazalicki–Peral

Five pairwise non-isomorphic one-parameter `Z/2Z × Z/6Z` families whose exact
generic rank 2 and full free generators are established in Theorem 2 of
Dujella–Kazalicki–Peral (2021).

## Variants

| Variant | Paper | Injective control |
| --- | --- | ---: |
| Dujella–Peral I | §8.1 | `u=15` |
| Dujella–Peral II | §8.2 | `u=17` |
| Dujella–Peral III | §8.3 | `u=22` |
| Hadano / Dujella–Peral IV | §8.4 | `u=19` |
| New | §8.5 | `u=20` |

The paper states that MacLeod's seven 2014 examples are all isomorphic to one
of the first three, so they are not duplicated here.

For §8.4 Rank Hunter uses the final replacement point `Q`, not the earlier
point `P`: the paper notes that `P` lies in `2E(Q)` and replaces it by a
half-point modulo torsion so that the displayed pair generates the full free
part.

## §8.3 reconstruction

The PDF text layer drops four middle coefficients from the printed expanded
`aa3` line. The plugin does not guess them. They are reconstructed exactly
from the same section's printed rank-1 coefficient
`a2(w)`, the printed base change
`w=(u^2-30u+180)/(3(u^2-180))`, and the clearing scale.
A regression checks that both reconstructed `aa3` and printed factored
`bb3` agree exactly with that source construction.

## Search

Every variant supports Candidate Generation, Family Search and Target Search.
The shared write-free runner reconstructs the selected variant's two full
published generators, performs bounded completed-square ratpoints stages, and
returns typed point artifacts. Rank Hunter core owns validation, exact
independence certification, persistence, and rank promotion.

## Source

Andrej Dujella, Matija Kazalicki, Juan Carlos Peral,
*Elliptic curves with torsion groups Z/8Z and Z/2Z × Z/6Z*,
RACSAM 115 (2021), Article 169; arXiv:2105.06215.
