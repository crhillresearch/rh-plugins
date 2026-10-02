# Provenance and claim ledger

## Exact construction

For the fixed sextuple

```text
348, -600, -216, 492, 876, -900
```

`family.py` implements Mestre's polynomial construction with

```text
q_t(x) = p6(x-t) p6(x+t)
G_t(x)^2 - q_t(x) = (539136 t)^2 r_t(x).
```

Thus the normalized quartic `y^2 = r_t(x)` carries twelve exact rational base fibres. One is used as the elliptic origin; the remaining eleven are exposed as section points.

The normalized quartic is even in `t`, so `t` and `-t` are exactly the same native quartic search target. Candidate generation/search therefore canonicalizes this orbit rather than spending work twice.

## Status

- Native quartic identity: **exact arithmetic**, with symbolic validator in `family.py`.
- Base fibres/section on-curve checks: **exact arithmetic**.
- PGL2/Möbius transforms and inverse mapping: **exact arithmetic**.
- Canonical-height projection residual: **numerical screen only**.
- Exact quadratic-character certificate: **rigorous lower-bound promotion mechanism used by the worker**.
- Public control specializations recorded in the manifest: **external controls**, not generic proof claims.

The code must not promote numerical novelty to a theorem-level rank claim.

## Rank Hunter 0.9.2 certificate

The release records Mestre's rank-at-least-11 result as historical provenance and independently exact-certifies the eleven reconstructed sections at t=1 before accepting verified generic lower bound 11. This certificate proves only the generic lower bound; every rational specialization still requires its own exact rank evidence.
