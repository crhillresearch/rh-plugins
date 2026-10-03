# Elkies X1092 · Published MW17 · v1.3.0

Rank Hunter Family plugin for the published Mordell-Weil rank-17 elliptic K3 fibration in Noam D. Elkies, *An elliptic K3 surface X/Q(t) with Mordell-Weil rank 17, I: Formulas for X and base changes of ranks 18 and 19*.

Release-audited for Rank Hunter **0.9.2**.

## Published source

- arXiv: https://arxiv.org/abs/2608.25406
- DOI: 10.48550/arXiv.2608.25406
- arXiv submission: 26 August 2026
- main rank-17 statement: Theorem 4 and §2.2.

The fibration is

```text
y^2 = x^3 - 27*S(t)*x + 27*T(t)/4
```

and the plugin bundles the exact published MW17 basis as sections `S1..S17`.

Elkies computes the height-pairing Gram matrix of those sections. Its determinant is `948`, so the 17 sections are independent. The paper also states that rank 17 is the largest possible Mordell-Weil rank over `Q(t)` for an elliptic K3 surface.

## Rank Hunter verification

The Family module does not rely only on manifest metadata.

`validate_generic_rank_claim()`:

1. reconstructs the exact 17 generic sections;
2. verifies all 17 on the generic curve over `Q(t)`;
3. recomputes the height pairing directly from the bundled section formulas;
4. requires entry-for-entry equality with the published 17×17 Gram matrix;
5. requires determinant `948`.

That verifies the operational generic lower bound used by Rank Hunter 0.9.2.

## Specialization boundary

The generic theorem is not copied blindly to a rational specialization.

For a specialization `t=t0`, Rank Hunter evaluates `S1..S17` exactly on the specialized curve. A rigorous specialization lower bound is promoted only through the ordinary exact independence-certificate path.

Nagao scores remain search heuristics only.

## Why this is separate from Elkies Rank-17 K3

This package and **Elkies Rank-17 K3** represent the same published elliptic K3 fibration and the same rank-17 theorem.

They are retained as separate RELEASE Families because this X1092 package has a distinct Rank Hunter presentation:

- preserved `S1..S17` MW-basis metadata;
- canonical coefficient-vector labels;
- family-specific vectorized finite-field/Nagao scoring;
- large-denominator sampled record-scan presets.

It is not presented as a second independent mathematical rank-17 construction.

## X1092 / ICARM #724 distinction

The published X1092 fibration here is **not** assumed to be fiberwise identical to the generalized ICARM #724 fibration merely because both use the X1092 surface name.

Exact rational transport between elliptic fibrations would be required before sections or specialization evidence could be reused between them.

## RELEASE scope

This RELEASE package is deliberately **MW17-only** mathematically. It now includes direct subgroup-aware **Family Search** and **Target Search** over the published fibration, but still excludes the experimental quadratic rank-jump/base-change reconstruction tooling.

Earlier development copies also contained:

- Elkies equation (11) and equation (12) quadratic base-change variants;
- half-lattice / trace / quartic reconstruction tools;
- an experimental rank-jump pipeline transform.

Those are excluded from this curated package. **Elkies Rank-18 First Cover** is already published as its own RELEASE Family, and other quadratic-cover reconstruction work remains development material until separately audited.

## Candidate search

The default record scan samples exact reduced rationals through denominator `10^6`, then uses staged finite-field/Nagao rescoring:

```text
sample count = 250,000
sample seed = 1092
prime stages = 523,5000
stage keeps = 50,000,5,000
final candidates = 5,000
```

The `deep` preset increases the sample count to one million and adds the intermediate prime stage `2000`.

The Family module's vectorized `nagao_score_table(p)` is checked against exact Sage point counts at small primes in the release regression suite.

## Family Search and Target Search

v1.3.0 adds the missing operational search adapters without changing the published family or its proof boundary.

**Family Search** consumes the candidate file produced by Rank Hunter, specializes `S1..S17` exactly, optionally certifies that 17-point subgroup, runs staged ratpoints searches, stores exact rational hits, and promotes a larger rigorous lower bound only after an exact independence certificate succeeds.

**Target Search** runs the same subgroup-aware logic against one stored X1092 specialization. Its defaults search deeper ratpoints stages and allow more exact extra-point attempts than the ordinary Family Search profile.

Both paths:

- use the existing `elkies_x1092_rank17_family` source of truth;
- preserve the published `S1..S17` basis metadata;
- run against Rank Hunter's temporary plugin-search database path;
- treat ratpoints hits as candidate extras until exact independence is certified;
- do **not** restore the excluded quadratic rank-jump/base-change reconstruction tools.

## MW provenance contract

For every specialized basis point, `generic_section_metadata(t)` records:

```text
basis_label
coefficient_vector
search_label
trace_coordinates
leading_y_sign
```

For the bundled basis these are the 17 standard unit vectors corresponding to `S1..S17`.

## Validation

Focused release gate. Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/elkies_x1092_rank17/tests
```

The gate covers:

- exact symbolic section replay;
- exact published height-lattice verification;
- specialization metadata;
- vectorized Nagao scorer agreement with exact curve counts;
- current-core plugin and search-adapter validation;
- Family/Target command construction;
- RELEASE isolation from the quadratic rank-jump development tooling.

## Version history

### v1.3.0

Adds complete Family Search and Target Search support for the published MW17 fibration: exact S1..S17 specialization replay, optional baseline certification, staged ratpoints search, exact extra-point certification, package-local adapter commands, and focused release regressions. The excluded quadratic rank-jump tooling remains excluded.

### v1.2.0

Rank Hunter 0.9.2 release audit. Adds an exact generic-rank verification hook, refreshes Elkies provenance, and isolates the approved Published MW17 Family from the separately released/experimental quadratic rank-jump material.

### v1.1.0

Development package with the Published MW17 family plus experimental quadratic rank-jump variants and reconstruction tools.
