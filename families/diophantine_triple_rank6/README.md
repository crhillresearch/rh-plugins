# Dujella–Peral · Diophantine Triple Rank 6

This Family reconstructs the fully explicit §2.5 Dujella–Peral family induced
by a rational Diophantine triple with torsion `Z/2Z × Z/2Z` and exact generic
rank 6.

The paper prints the final model, six independent sections, and the associated
Diophantine quadruple. At `v=5` the Gusić–Tadić criterion is injective; the
paper concludes exact generic rank 6 and torsion `Z/2Z × Z/2Z`.

## Source-sign audit

The original paper/arXiv v2 prints the sixth x-coordinate with coefficient
`+9`. A later survey reprint shows `-9`. Exact substitution at `v=5`
resolves the discrepancy: the `+9` coordinate lies on the published curve;
the `-9` coordinate does not. Rank Hunter therefore follows the original
paper and regression-tests that sign.

## Other rank-6 base changes

§2.6 gives three additional rational base changes of the rank-4 parent and
states that they also produce rank-6 curves. The paper intentionally omits the
two extra section formulas for those cases. Rank Hunter records those formulas
in provenance as research leads but does **not** promote them to release
variants without a reconstructible six-point basis.

## Search

Candidate Generation, Family Search and Target Search are all supported.
Family/Target Search reconstructs the six published exact sections and then
runs bounded completed-square ratpoints stages for extras.

The runner writes no live scientific state; it emits typed point artifacts and
Rank Hunter core owns point validation, independence certification, persistence
and rank promotion.

The maintained prescribed-torsion table currently lists best known rank
`>=15` for `Z/2Z × Z/2Z`, so record-oriented searches target rank 16.

## Source

Andrej Dujella and Juan Carlos Peral,
*Elliptic curves induced by Diophantine triples*,
RACSAM 113 (2019), 791–806, DOI `10.1007/s13398-018-0513-0`,
arXiv `1712.02082v2`.
