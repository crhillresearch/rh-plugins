# Hill C₂ rank ≥11 genus-one-base family

This plugin pairs quadratic covers 10 and 13 of the C₂ elliptic K3 family at
`u = 11/5`. Each cover adds one independent section to the nine parent
sections. On their positive-rank genus-one compositum, the two new sections
are independent of each other and of the parent sections, giving a verified
generic rank lower bound of 11 with C₂ torsion.

The claim is over the genus-one function field. It is not an exact generic
rank claim over the original rational parameter line, and an individual
specialization needs its own exact rank evidence. The separate
[`hill_c2_generic_rank10_2026`](../hill_c2_generic_rank10_2026/) plugin exposes
the two rational rank-at-least-10 covers.

The `data/` directory contains the paired-cover equations, section data, and
rank-11 certificate. The family and search adapter specialize this
construction for Rank Hunter; core checks points and owns rank promotion.
The source proof packet is in
[Rank Ledger](https://github.com/crhillresearch/rank-ledger/tree/main/c2-rank-11-genus-one-family).
