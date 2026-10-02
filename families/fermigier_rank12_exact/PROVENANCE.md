# Fermigier–Mestre K3 provenance and claim ledger

## Published literature

### Mestre rank-at-least-12 family

Jean-François Mestre, *Courbes elliptiques de rang ≥ 12 sur Q(t)*,
C. R. Acad. Sci. Paris Sér. I Math. 313(4) (1991), 171–174.

This is the literature anchor for the generic rank-at-least-12 construction.

### Fermigier rank-at-least-22 specialization

Stéfane Fermigier, *Une courbe elliptique définie sur Q de rang ≥ 22*,
Acta Arithmetica 82(4) (1997), 359–363.

DOI: `10.4064/aa-82-4-359-363`.

The paper presents the rank-at-least-22 example and the search methods that produced it.

## Public reproduction cross-check

A separate public Sage reproduction in
`MarcusBarnes/elliptic_rank_search` corroborates the specific reconstruction data used here:

- selected roots: `0,55,314,378,1007,1036`;
- paper parameter: `19754/39`;
- symmetric shift: `39508/39`;
- exact split-sextic square completion;
- twelve forced rational quartic points;
- Q-isomorphism of the resulting Jacobian with Fermigier's published rank-22 model.

That reproduction cites the published rank ≥22 result rather than re-proving its rank.

## Rank Hunter reconstruction

The plugin copies the normalized quartic formulas into Sage code and verifies exactly over `Q(u)`:

- the split-sextic square-completion identity;
- the twelve root-derived quartic points;
- Fermigier's thirteenth quartic point;
- the deterministic rational-origin Weierstrass mapping.

The current RELEASE validator additionally exact-certifies the twelve non-origin sections as independent at the good specialization `u=7/3`. This proves the generic lower bound 12.

## Frozen exact arithmetic rank theorem

The user's reconstruction artifact
`elliptic_fermigier_generic_rank_exact.json`
reports status **exact arithmetic generic-rank theorem** and arithmetic generic rank exactly 12 over `Q(u)`.

Frozen hashes recorded by that artifact:

- canonical adapter source SHA-256:
  `960678a1991f424694b99fcc8eff6100fdc93200c64588328d55ae95186529c8`
- frozen section certificate SHA-256:
  `94fc64d7f1744f6a20a0396d32914cd36330107db2538e03ee95cc3e32927051`
- section source SHA-256:
  `59742cd9c98f61e318ccb6f95e632ec4f84660e87222f4ed8f912bc5394f9596`
- generic-rank verifier SHA-256:
  `84fd1b08f742cb338e391b826b6f76f238ae377ad77e1b8d3bff85485e5ddb14`

The artifact reports:

- arithmetic generic rank: exactly 12;
- arithmetic proof status: unconditional;
- geometric generic rank interval: `[12,13]`;
- Tate conjecture assumed: false.

These hashes are preserved as provenance. The RELEASE package does not claim that hashes alone constitute a rerun of the upper-bound theorem.

## Rank Hunter 0.9.2 claim separation

- published Mestre/Fermigier literature: historical mathematical provenance;
- twelve generic sections: exact symbolic construction plus exact generic independence certificate;
- `verified_generic_rank_lower=12`: operational Rank Hunter certificate;
- exact arithmetic upper bound 12: frozen reconstruction-theorem provenance;
- Fermigier rank-22 fiber: published historical control;
- Nagao / height-residual scores: heuristic scheduling evidence;
- specialized lower bounds: promoted only after exact Rank Hunter independence certification.

No specialization rank is assigned from generic or historical metadata alone.
