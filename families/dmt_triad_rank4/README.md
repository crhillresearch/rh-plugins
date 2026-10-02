# DMT Triad Family · v0.1.3

Rank Hunter Family plugin for REA CURVE2 / Triad Family from C. R. Hill, *Regularity-Selected Generic Rank at Least Four in the Piezas Diophantine Sextuple* (DMT-001, preprint, 2026-09-12).

Paper: https://hillaxiom.com/papers/dmt-001.pdf

Release-audited for Rank Hunter **0.9.2**. The Family mathematics and search paths are standalone; no checkout of the private research repository is required for normal Family use.

## Family

DMT-001 starts from the Piezas one-parameter rational Diophantine sextuple
`{a(t), b(t), c(t), d(t), e(t), f(t)}` and its regularity relations.

The selected triads are exactly:

`ace, acf, bde, bdf, bef, cef`.

For a selected triad `{u,v,w}`, the plugin uses

`y^2 = (x + uv)(x + uw)(x + vw)`.

Its long Weierstrass invariants are

`[0, uv+uw+vw, 0, uv*uw+uv*vw+uw*vw, uv*uw*vw]`.

The roots `-uv,-uw,-vw` give full rational 2-torsion on every nonsingular selected fiber.

## Four explicit generic sections

| Variant | Four supplied sections |
| --- | --- |
| ACE | P, R, E_d, E_f |
| ACF | P, R, E_d, E_e |
| BDE | P, R, E_c, E_f |
| BDF | P, R, E_c, E_e |
| BEF | P, R, E_c, E_d |
| CEF | P, R, E_a, E_b |

Each variant declares `verified_generic_rank_lower = 4`. Rank Hunter verifies that operational claim at the good control fiber `t=12/5` using an exact independence certificate for the four displayed sections.

Any integral relation among the generic sections would specialize to a relation at a good fiber, so exact independence after specialization verifies generic independence.

This does **not** make every specialization rank exactly four. Specialized curves retain Rank Hunter's rigorous-lower / rigorous-upper / exact-rank separation.

## CEF high-rank certificate bundles

The CEF variant includes frozen exact rational point bundles from prior DMT research artifacts:

- the rank-10 source specialization at `t=-327/136` and its canonical alias `-463/191`;
- one historical rank-9 bundle;
- historical rank-8 bundles preserved by exact CEF model identity.

These bundles are **candidate evidence**, not automatic proof. The stored external rank/artifact metadata is provenance and scheduling context only; Rank Hunter must independently exact-certify the imported point bundle before it can promote a rigorous lower bound.

The CEF certificate helpers deliberately return nothing for unrelated parameters such as the generic control fiber `12/5`.

## Rank Hunter workflow

CEF is the default variant as a practical search default; it is not claimed to have a stronger generic theorem than the other five variants.

1. Validate and activate **DMT Triad Family**.
2. Choose ACE, ACF, BDE, BDF, BEF, or CEF.
3. Generate a rational-parameter candidate pool.
4. Run Family Search. The adapter delegates screening/descent to core `rank42.auto_analyze` while retaining the four explicit DMT sections.
5. Replay stored fibers through Target Search using the same Family-aware analyzer.

## Optional curves2 research corpus

The **DMT Rank-Jumps Corpus** is optional. Family generation, Family Search, Target Search, and generic-rank validation do not depend on it.

The installer normally downloads the latest successful `curves2-db` artifact from the dedicated DMT workflow, validates the SQLite schema, and requires non-empty curve/observation evidence before atomically replacing the local cache. A full historical artifact-ledger rebuild remains available as a fallback.

The artifact source is the private `crhillresearch/dmt-rank-jumps` repository, so corpus installation/rebuild requires authenticated access to that repository.

## Source correspondence

The standalone Family formulas were release-audited against:

- `dmt_rank_jumps/family.py` — Piezas sextuple, regularity identities, and selected triads;
- `dmt_rank_jumps/points.py` — split cubic, P, R, E_z, and four-section table;
- `tests/test_paper_baseline.py` — `t=12/5` control fiber and selected-triad baseline.

Mathematical source commit: `3f53baaedcbdb852e2e999578bf0f75850ad3e5f`.

The release audit baseline for the newer certificate/corpus-enabled plugin was:
`36d37730ded550a04ceb383434c466afd81e54c9`.

## Validation

Focused release gate. Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

`PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/dmt_triad_rank4/tests`

This includes the generic-rank controls, exact CEF certificate-bundle model checks, corpus installer validation, adapter behavior, and full current-core validation across all six variants.

## Version history

### v0.1.3

Release audit for Rank Hunter 0.9.2, rebased onto the certificate/corpus-enabled v0.1.2 baseline. Preserves the CEF rank-10/rank-9/rank-8 point bundles and validated curves2 installer while tightening public-release provenance and proof-boundary wording.

### v0.1.2

Added frozen CEF high-rank point bundles, stable CEF Nagao cache identity, manifest-owned search options, and validated prebuilt `curves2` corpus installation with rebuild fallback.

### v0.1.0–0.1.1

Initial six-variant DMT Triad Family and early compatibility updates.
