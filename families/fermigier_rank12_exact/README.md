# Fermigier–Mestre K3 · v1.1.0

Rank Hunter Family plugin for the one-parameter Mestre/Fermigier high-rank K3 reconstruction with canonical Rank Hunter parameter `u` and symmetric shift `s=2u`.

Release-audited for Rank Hunter **0.9.2**.

## Published literature boundary

Two literature results anchor this package:

1. Jean-François Mestre, *Courbes elliptiques de rang ≥ 12 sur Q(t)*, C. R. Acad. Sci. Paris Sér. I Math. 313(4) (1991), 171–174. This is the published rank-at-least-12 family result.
2. Stéfane Fermigier, *Une courbe elliptique définie sur Q de rang ≥ 22*, Acta Arithmetica 82(4) (1997), 359–363, DOI `10.4064/aa-82-4-359-363`. This is the published rank-at-least-22 specialization result.

Fermigier's 1997 paper describes the search leading to the rank-22 curve; it does **not** serve as the source of the later Rank Hunter reconstruction claim that this particular arithmetic generic model has exact rank 12.

## Reconstructed fixed-root model

The release package uses the selected roots

```text
0, 55, 314, 378, 1007, 1036
```

and the exact square-completion construction behind the Fermigier search.

For Rank Hunter parameter `u`:

```text
s = 2u
q(x) = p6(x-s) p6(x+s)
q(x) = g(x)^2 - (101232*u)^2 r_u(x)
```

so the normalized genus-one quartic is

```text
y^2 = r_u(x).
```

The twelve shifted roots give twelve rational quartic points, and the package carries Fermigier's thirteenth exact quartic point. One point is chosen as the genus-one origin, leaving twelve exact sections on the deterministic Weierstrass model.

An independent public Sage reproduction of Fermigier's rank-22 example also uses these six roots, paper parameter `19754/39`, and symmetric shift `39508/39`.

## Generic-rank claim boundary

The manifest now distinguishes what Rank Hunter can verify operationally from the stronger frozen reconstruction theorem provenance.

### Operational release certificate

Rank Hunter declares

```text
historical_generic_rank_lower = 12
verified_generic_rank_lower = 12
generic_rank_claim_state = generic_lower_bound_verified
```

The validator specializes the twelve explicit sections at the good control `u=7/3` and runs Rank Hunter's exact independence certificate.

Exact independence at one good specialization proves the twelve generic sections independent: any integral relation over `Q(u)` would specialize to the same relation at that fiber.

Thus the RELEASE package independently verifies **generic rank at least 12**.

### Frozen exact-rank theorem provenance

The reconstruction artifact

`elliptic_fermigier_generic_rank_exact.json`

reports:

- arithmetic generic Mordell–Weil rank over `Q(u)`: exactly 12;
- arithmetic status: unconditional;
- geometric generic rank over `Qbar(u)`: in `[12,13]`;
- Tate conjecture assumed: false.

Its frozen source/verifier hashes are preserved in `PROVENANCE.md`.

That upper-bound theorem is **provenance**, not a fresh Rank Hunter 0.9.2 certificate. The current release validator proves the lower bound 12; it does not pretend to reconstruct the upper-bound proof from hashes alone.

## Fermigier rank-22 control

The release keeps

```text
u = 19754/39
s = 39508/39
```

as the historical Fermigier rank-22 control for this reconstruction.

This is a control/provenance record. Matching the parameter does not automatically assign a specialization rank in Rank Hunter.

A second internal search anchor remains `u=28917/20`; it is not presented as a published Fermigier parameter.

## Search geometry

The Family supports:

- candidate generation;
- Family Search;
- Target Search;
- the exact twelve-section known subgroup;
- native quartic search;
- exact PGL2 chart search;
- free search.

The native quartic is invariant under `u -> -u`, so candidate generation/search canonicalizes that orbit.

Subgroup height residuals are numerical scheduling evidence only. PGL2 transforms, quartic inverse maps, rational point membership, and rank promotion are exact. Rank Hunter raises a rigorous specialization lower bound only after exact certificate replay.

## Validation

Focused release gate. Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/fermigier_rank12_exact/tests
```

The release gate checks:

- the exact split-sextic/quartic formulas;
- all thirteen generic quartic points;
- sign symmetry `u ~ -u`;
- exact generic lower-bound-12 certification;
- current-core plugin/adapter validation;
- native/PGL2 local runner layout;
- subgroup scheduling regressions.

## Version history

### v1.1.0

Rank Hunter 0.9.2 release audit. Separates published literature, exact reconstruction, operational generic lower-bound certification, and frozen exact-rank theorem provenance; removes stale 0.8.x wording and adds a current-core release gate.

### v1.0.2

Development package for the reconstructed exact-rank-12 research workflow.
