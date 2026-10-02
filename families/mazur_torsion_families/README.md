# Mazur Torsion Families · v0.1.5

Rank Hunter Family plugin providing prescribed-torsion search lanes for every rational torsion group allowed over `Q` by Mazur's theorem.

Release-audited for Rank Hunter **0.9.2**.

## Classification boundary

Mazur's rational torsion theorem says that for an elliptic curve over `Q`,

```text
E(Q)_tors ≅ C_n                  for 1 <= n <= 10 or n = 12
E(Q)_tors ≅ C2 × C_{2m}         for 1 <= m <= 4.
```

That gives exactly 15 possibilities:

```text
Trivial
C2, C3, C4, C5, C6, C7, C8, C9, C10, C12
C2 × C2, C2 × C4, C2 × C6, C2 × C8
```

Mazur classifies the possible groups. The one-parameter search models in this plugin come from Tate/Kubert normal forms, the Legendre family, and exact full-2-torsion lifts; they are not attributed to Mazur himself.

## Universal models versus direct search slices

The manifest deliberately distinguishes two provider roles.

### Canonical universal lanes

The package treats these as its canonical one-parameter prescribed-torsion models:

```text
C4, C5, C6, C7, C8, C9, C10, C12
C2 × C4, C2 × C6, C2 × C8
```

The cyclic families use Kubert–Tate normal form with the marked torsion point `P=(0,0)`.

The noncyclic families impose exact splitting conditions on the remaining 2-division factor:

- C2 × C4: `alpha=(t^2-1)/16`;
- C2 × C6: `alpha=2(5-t)/(t^2-9)`;
- C2 × C8: `alpha=2(t+4)/(8-t^2)`.

### Direct prescribed-torsion slices

The following are useful direct search lanes but are **not** advertised as exhaustive moduli parameterizations:

```text
Trivial
C2
C3
C2 × C2
```

The C2 × C2 lane is a Legendre-type full-2-torsion slice. Low-level torsion and twist normalization make it safer to describe these as search slices rather than pretend every Q-isomorphism/twist class is represented exactly once.

## Exact torsion proof gate

A family formula is only a routing device.

For every generated specialization Rank Hunter's torsion workflow computes the **exact rational torsion subgroup** before the curve can count toward a prescribed-torsion campaign.

The release self-check independently instantiates every one of the 15 variants at its declared validation parameter and asks Sage for the exact torsion subgroup. Validation fails if:

- the specialization is singular;
- the exact torsion label is not the selected group;
- the torsion order and invariant factors disagree.

No generic rank is declared by this plugin.

## Record-hunting metadata

The manifest stores current record lower bounds and a default next-rank goal. These are search targets only.

The table was checked against Andrej Dujella's live *High rank elliptic curves with prescribed torsion* table on **2026-10-02**:

| Torsion | record lower | default goal |
|---|---:|---:|
| Trivial | 31 | 32 |
| C2 | 20 | 21 |
| C3 | 15 | 16 |
| C4 | 13 | 14 |
| C5 | 9 | 10 |
| C6 | 9 | 10 |
| C7 | 6 | 7 |
| C8 | 6 | 7 |
| C9 | 4 | 5 |
| C10 | 4 | 5 |
| C12 | 4 | 5 |
| C2 × C2 | 15 | 16 |
| C2 × C4 | 9 | 10 |
| C2 × C6 | 6 | 7 |
| C2 × C8 | 3 | 4 |

Those numbers never certify a newly generated curve.

A candidate contributes to a record hunt only after:

1. the specialization is nonsingular;
2. exact Sage torsion equals the selected target group;
3. every rigorous rank lower bound comes from exact rational points plus an exact independence certificate.

Nagao scores, record metadata, provider roles, and search presets are scheduling evidence only.

## C2 × C8 targeted attacks

C2 × C8 remains the default variant because the current record lower bound is 3 and Rank Hunter has a dedicated escalation stack for exact-torsion target curves.

Its plugin-owned target buttons route into current core Pipeline recipes including:

- Deep;
- Fiber Expansion;
- Generator Breaker;
- Geometry Grinder;
- Selmer Gate;
- Covering Forest;
- 2-Isogeny Hunt;
- Arithmetic Siege.

Rank Hunter inserts **Exact Torsion** ahead of the point/rank stages. Isogenous children keep separate evidence records even though rational rank is invariant under Q-isogeny.

## Current-core ownership

This plugin exposes `candidate_generation` only. It does not carry a family-native Target Search adapter.

Rank Hunter 0.9.2 core owns:

- exact torsion computation and persistence;
- torsion-provider routing;
- record/goal extraction from `torsion_record`;
- Target's exact-torsion-first Pipeline;
- exact point/rank evidence;
- Pipeline presets and escalation.

The plugin owns:

- the 15 family formulas;
- exact target torsion labels;
- provider-role metadata;
- record-target metadata;
- search presets.

## Sources

Classification:

- Barry Mazur, *Modular curves and the Eisenstein ideal*, Publ. Math. IHÉS 47 (1977), 33–186.

Parameterizations:

- Daniel S. Kubert, *Universal bounds on the torsion of elliptic curves*, Proc. London Math. Soc. (3) 33(2) (1976), 193–237, DOI `10.1112/plms/s3-33.2.193`;
- Tate normal form;
- Legendre full-2-torsion family.

Record table:

- Andrej Dujella, *High rank elliptic curves with prescribed torsion*.

## Validation

Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout, then from the plugin repository run:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/mazur_torsion_families/tests
```

The release gate covers:

- all 15 Mazur groups exactly once;
- exact Sage torsion at all 15 validation fibers;
- universal/direct-slice role labeling;
- current record/goal metadata;
- current-core plugin validation and torsion-routing helpers;
- C2 × C8 Target preset proof-gate metadata;
- README path hygiene.

A direct exact torsion self-check is also available:

```bash
sage -python families/mazur_torsion_families/verify_plugin.py
```

## Version history

### v0.1.5

Rank Hunter 0.9.2 release audit. Refreshes Mazur/Kubert/Dujella provenance, rechecks the live record table, adds exact all-15 torsion/current-core release validation, corrects the C2 × C2 slice description, and documents the exact-torsion-first evidence boundary.

### v0.1.4

Added the full 15-group prescribed-torsion provider set, record-hunt metadata, manifest-owned search presets, and C2 × C8 Pipeline escalation presets.
