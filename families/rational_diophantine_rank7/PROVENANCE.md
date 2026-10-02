# Provenance — Rational Diophantine Triple Rank ≥7

Primary source: Dujella–Peral (2020), §3, equations (7)–(13).

The rank-7 construction intersects the second and third rank-6 substitutions
of the common rank-4 parent. Conditions (8) and (9) imply the genus-1 quartic

`z^2 = 54w3^4 + 2736w3^3 + 66592w3^2 + 2987712w3 + 64393056`.

The paper identifies this quartic with an elliptic curve of rank 3, proving
infinitely many rational base points.

Curve (12) supplies six independent sections x31,...,x36. For a pair
`(w2,w3)` satisfying condition (8) or (9), curves (11) and (12) are explicitly
isomorphic. The paper observes that the first five point ratios match while
x36 does not match x26, so transporting x26 gives the seventh x-coordinate

`x7 = x26 * a63/a62`.

Rank Hunter reconstructs exactly that formula.

At `(w2,w3)=(-76/3,26)`, the plugin reproduces the paper's specialized curve

`y^2 = x^3 - 163531808801344950045916528640000 x^2
       + 6680706316011654681276493655189069731350803361465165152256000000 x`

and the seven printed independent x-coordinates. This exact specialization is
used only to certify the operational generic lower bound 7 over the elliptic
base; exact generic rank 7 is not claimed.

A second infinite rank>=7 construction from substitutions 2 and 5 is also
proved in the source, with control `(w2,w5)=(6392/99,6392/99)`. The source
does not print the explicit transported seventh-section expression for that
case, so Rank Hunter does not manufacture it as a release variant.

Candidate Generation's finite-field model rejects residues for which the base
quartic is nonsquare. This is a local-solubility filter, not proof of a rational
base point; exact rational square checking in `curve(w3)` remains authoritative.
