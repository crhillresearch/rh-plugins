# Elkies Rank-18 First Cover · v0.1.1

Rank Hunter Family plugin for the first explicit quadratic base change in Noam D. Elkies, *An elliptic K3 surface X/Q(t) with Mordell-Weil rank 17, I: Formulas for X and base changes of ranks 18 and 19* (arXiv:2608.25406v1).

Release-audited for Rank Hunter **0.9.2**.

## Published source

Elkies proves that the rank-17 K3 fibration has rational quadratic base changes whose Mordell-Weil rank is at least 18. In §3 he gives one of the simplest examples as equation (11):

```text
u^2 = 4225*t^2 + 38636*t + 289444
```

The leading coefficient is `4225 = 65^2`, so the conic has rational points at infinity. Rank Hunter uses the rational parameterization

```text
t = (289444-r^2)/(130*r-38636)
u = 65*t+r
```

and therefore represents the base-changed family over `Q(r)`.

Source:
- https://arxiv.org/abs/2608.25406
- DOI: 10.48550/arXiv.2608.25406
- theorem/source boundary: Theorem 3(a), Lemma 7, §3 equation (11), Proposition 8.

## Rank-17 dependency

This package intentionally reuses the released **Elkies Rank-17 K3** package for the exact base surface and the published sections P01..P17.

The required sibling file is:

```text
families/elkies_rank17_2026/family.json
```

The RELEASE branch publishes Rank-17 before Rank-18, so this dependency is explicit and deterministic rather than duplicated.

## P18 reconstruction

Elkies's paper proves that a rational quadratic section contributes a new independent direction after base change. The paper does **not** print the P18 coordinates used by this plugin.

Rank Hunter carries an independently recovered P18 with coordinates of the form

```text
x = x0(t) + x1(t)u
y = y0(t) + y1(t)u
```

and does not trust that reconstruction by declaration alone.

The release validator checks exactly over `Q(t,u)` with
`u^2 = 4225*t^2 + 38636*t + 289444` that:

- P18 lies on the base-changed curve;
- its Galois conjugate is obtained by `u -> -u`;
- P18 is not Galois invariant;
- `P18 + conjugate(P18)` equals the stored exact trace combination of P01..P17.

The family is then rationally parameterized over `Q(r)`, where all 18 sections are checked again exactly.

## Generic-rank claim boundary

The manifest declares:

```text
verified_generic_rank_lower = 18
generic_rank_claim_state = generic_lower_bound_verified
```

This is a **generic lower bound**, not an assertion that every rational specialization has rank 18.

For each specialization Rank Hunter separately:

1. instantiates all 18 sections exactly;
2. optionally exact-certifies their specialized independence;
3. promotes a rigorous specialization lower bound only after that certificate succeeds;
4. treats any additional `ratpoints` hit as a candidate until exact independence certification.

## Search support

The Family supports:

- candidate generation;
- Family Search;
- Target Search;
- known-subgroup use;
- free search;
- optional multiscale Nagao rescoring.

The multiscale rescorer is heuristic priority evidence only. It does not write rank evidence or run descent.

## Validation

Focused release gate. Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/elkies_rank18_2026/tests
```

The gate includes:
- paper/provenance contract checks;
- exact quadratic-cover P18 verification;
- exact 18-section symbolic validation after rational parameterization;
- current-core plugin validation;
- adapter Family/Target command wiring.

## Version history

### v0.1.1

Rank Hunter 0.9.2 release audit. Strengthens P18 verification in the actual quadratic cover field, documents the Rank-17 sibling dependency and published/reconstructed boundary, refreshes provenance, and adds package-local current-core regressions.

### v0.1.0

Initial Elkies first-cover package with rational parameterization, 17 pulled-back published sections, recovered P18, subgroup-aware search, and multiscale rescoring.
