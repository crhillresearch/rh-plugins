# Hill Rank-19 K3

This plugin implements C. R. Hill's paper, [*Nineteen Independent Sections
from Two Quadratic Covers of an Elliptic K3 Surface*](https://hillaxiom.com/papers/k3-19-sections.html).
The base elliptic K3 fibration has 17 independent sections. The two
quadratic covers, indexed 4339 and 36773 in the proof data, add one section
each. On their genus-one compositum the 19 sections are independent.

The search parameter is a nonzero integer `n`, representing the point `nP`
on the auxiliary genus-one curve. The family maps that point exactly to a
rational parameter on the K3 fibration. Its family search adapter specializes
the 18 sections from the first cover and the additional section from the
second cover, then Rank Hunter checks the points and certifies independence on
each individual fiber. The target adapter also supports exact point searches
on a selected elliptic curve.

The map to the K3 parameter is invariant under the auxiliary involution
`Q -> P-Q`. Thus integer inputs `n` and `1-n` give the same fiber; candidate
generation keeps the representative `n >= 1` and later AI rounds exclude
fibers already searched.

Every generated pool reserves a slot for `n=1`, a reproducible fiber of the
rank-19 construction. Rank Hunter certified rank at least 19 for this fiber
in its first AI Hunt. The separate parent-family curve at `t=15122/33609`
has a rank-at-least-27 certificate; this does not identify it with `n=1`.

The generic statement is a lower bound over the function field of the
genus-one parameter curve. Individual fibers are promoted only after their
own exact evidence is checked. The construction and section coordinates are
documented in the paper and proof packet:

- Paper: `https://hillaxiom.com/papers/k3-19-sections.html`
- Proof data and verifier: `https://github.com/crhillresearch/rank-ledger/tree/main/rank-19-genus-one-base-change`
