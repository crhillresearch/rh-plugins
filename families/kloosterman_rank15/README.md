# Kloosterman Rank-15 K3 · v1.1.0

Rank Hunter Family plugin for Remke Kloosterman's explicit elliptic K3 surface of Mordell-Weil rank exactly 15 over `Q(t)`.

Release-audited for Rank Hunter **0.9.2**.

## Published source

Remke Kloosterman, *Elliptic K3 Surfaces with Geometric Mordell-Weil Rank 15*, Canadian Mathematical Bulletin 50(2) (2007), 215–226.

- arXiv: https://arxiv.org/abs/math/0502439
- DOI: 10.4153/CMB-2007-023-2
- theorem implemented here: **Theorem 1.2**

The plugin specializes exactly

```text
y^2 = x^3
    + 2(t^8 + 2t^4 + 1)x
    - 4t^2(t^8 - 6t^4 + 1).
```

Kloosterman's Theorem 1.2 proves that this explicit elliptic K3 surface over `Q` has Mordell-Weil rank **15** over `Q(t)`.

## Important source distinction

The paper's abstract displays a different surface,

```text
y^2 = x^3
    + 2(t^8 + 14t^4 + 1)x
    + 4t^2(t^8 + 6t^4 + 1),
```

and states that it has **geometric** Mordell-Weil rank 15.

This Rank Hunter Family does **not** implement that abstract surface. It implements the rational Theorem 1.2 surface above, whose Mordell-Weil rank over `Q(t)` is proved to be exactly 15.

## Proof boundary

Kloosterman's argument is geometric rather than a printed 15-section basis suitable for immediate Rank Hunter replay. The proof obtains rank at least 15 from the construction, then proves the required Picard-number upper bound using reductions at two good primes and an Artin–Tate discriminant comparison.

The current plugin package does **not** bundle an explicit 15-section `Q(t)` basis, a plugin-local height lattice for those sections, or a current-core `validate_generic_rank_claim()` certificate.

Accordingly, the release manifest deliberately keeps

```text
historical_generic_rank_lower = 15
generic_rank_claim_state = historical_record
```

with no `verified_generic_rank_lower`.

This is conservative Rank Hunter evidence handling: the paper's exact theorem remains visible provenance, but it is not silently converted into a specialization lower bound.

## Specialization boundary

A rational fiber `t=t0` does not inherit rank 15 merely because the generic family has rank 15.

Family Search therefore runs with `--no-generic-witness` and uses core PARI-first quick screening / bounded mwrank fallback only. Rigorous specialization lower bounds must come from actual specialization evidence in Rank Hunter's point/evidence ledger. Target Search uses the ordinary fixed-curve exact point/certificate path.

## Search support

The release supports candidate generation, Family Search, Target Search, and free search. The active manifest preserves the current `casual`, `scan`, `widen`, and `deep` presets.

The model is even in `t`, so `t` and `-t` give the same specialization. For nonzero `t`, reciprocal parameters give Q-isomorphic specializations after the usual Weierstrass scaling. The candidate defaults remove the sign duplicate by searching positive parameters; reciprocal quotienting is not automatic.

## Validation

Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout, then from the plugin repository run:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/kloosterman_rank15/tests
```

The release gate checks the exact Theorem 1.2 model, the historical-only generic claim contract, current-core plugin validation, current Family/Target command flags, and README path hygiene.

## Version history

### v1.1.0

Rank Hunter 0.9.2 release audit. Refreshes Theorem 1.2 provenance, distinguishes the abstract geometric-rank surface from the implemented Q-rational surface, preserves exact-rank-15 as literature provenance only, removes stale 0.8.x/install-package wording, and adds current-core release tests.

### v1.0.2

Moved Family Search to Rank Hunter core's PARI-first quick-screen path and retained the published rank-15 result as historical metadata only.
