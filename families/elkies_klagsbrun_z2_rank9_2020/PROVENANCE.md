# Provenance and claim ledger

## Primary source

Noam D. Elkies and Zev Klagsbrun, *New Rank Records For Elliptic Curves Having Rational Torsion*, Open Book Series 4 (2020), 233–250.

- arXiv: 2003.00077
- DOI: 10.2140/obs.2020.4.233
- arXiv submission: 28 February 2020.

## Source-derived mathematics

Section 9 gives the rational-2-torsion elliptic K3 fibration

`y^2 = x^3 + 2 A x^2 + B x`

with `B=∏B_i`, the symmetry `E_u ≅ E_{-u}`, and the admissibility statement: when `5-u^2` is a square and `u != ±1,±2`, the Mordell–Weil group over `Q(t)` is `Z/2Z × Z^9`.

Appendix A gives the generator x-coordinates / rank-9 lattice data used to construct the nine bundled sections.

Section 9 also reports:
- `u=2/5`, rank-19 specialization at native `t=11860/97527`;
- `u=11/5`, rank-20 specialization at native `t=-721141/2026305`;
- another rank-19 `u=11/5` specialization whose transformed/native pair is consistent with the stated Möbius map;
- no specialization above rank 18 found in the searched regions for `u=2/13` and `u=22/13`.

Appendix B.2 gives the rank-20 minimal model and 20 generator x-coordinates.

## Implementation-derived exact data

The paper gives generator x-coordinates rather than complete `(x,y)` rational functions for each fixed-`u` Rank Hunter representation.

The package derives compatible rational y-functions exactly and validates all nine sections symbolically over `Q(t)` for each native branch/search representation.

The transformed `u=11/5` search family is exactly the native family after

`native_t = (2-s)/(s-6)`.

## Rank-20 chart discrepancy

The source prints transformed `t=-68559/32629` together with native `t=-721141/2026305`.

Those values do not satisfy the stated Möbius map.

Exact inversion of the native value yields `-68559/326291`, which does satisfy the map. The source-printed value remains preserved in `data/published_controls.json`; the exact map-consistent value is stored separately and used operationally.

The published rank-19 pair `100782/104143 -> -26876/131019` is exactly consistent with the same map.

## Rank Hunter 0.9.2 ownership

Core owns:
- exact PGL2 chart/native parameter persistence and fingerprints;
- canonical native-family identity and cross-chart deduplication;
- mapping exact generic sections to stored models before certification;
- rigorous point/evidence ledgers and Target Search starting bases.

The plugin owns:
- the fixed-`u` family mathematics;
- the published Möbius chart declaration;
- published control/provenance fixtures;
- Family/Target command assembly.

## Claim boundaries

- generic rank 9 / `Z/2Z × Z^9`: published source mathematics;
- bundled generic sections: exact-symbolically verified by Rank Hunter;
- specialized baseline: promoted only after exact independence certification;
- Nagao score: heuristic only;
- exact rational-point hit: not automatically an independent rank direction;
- rank-20 fixture: published exact-rank provenance/control, never an automatic database assignment.

## Release hygiene

The development package contained an absolute local symlink named
`elkies_klagsbrun_z2_rank9_2020` pointing to a developer-local path.
It is not scientific content and is removed from the curated RELEASE package.
