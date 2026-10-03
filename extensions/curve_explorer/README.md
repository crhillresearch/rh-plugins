# Curve Explorer v0.5.0

Interactive Rank Hunter extension for inspecting the real locus of a stored elliptic curve while keeping rational-point arithmetic exact over **Q**.

## v0.5.0 highlights

- Added page-level **Graph** and **3D** views.
- **Graph** is the existing exact real-locus explorer and group-law workspace.
- **3D** samples the complex affine curve and renders an interactive projection to real 3-space:
  - `(Re x, Im x, Re y)`
  - `(Re x, Im x, Im y)`
- The 3D view has drag-orbit, wheel zoom, reset, auto-rotate, real-locus highlighting, and stored rational-point overlays.
- The complex visualization is explicitly presentation-only: it is not rank evidence, omits the point at infinity, and projected self-intersections need not be singularities of the elliptic curve.

## Validation

From the Rank Hunter project root:

```bash
pytest -q plugins/curve_explorer/tests
```

The regression suite covers exact generalized-Weierstrass arithmetic, SQLite-row conversion, exact third-intersection/negation data, point-category conservatism, robust framing, and the bounded exact click-construction cache.

## Inspiration

The interaction and teaching-oriented presentation were inspired by **@alozanoroble** and the MATH5020 **Rational Points on Elliptic Curves** app:

https://alozanoroble.github.io/MATH5020-Elliptic_Curves/apps/rational-points/

Curve Explorer is an independent Rank Hunter implementation adapted to stored generalized Weierstrass models, exact rational arithmetic, Rank Hunter point metadata, and the project's proof/evidence boundaries.

## 3D inspiration

The complex-curve projection is inspired by the visualization approach on Arapura's Purdue elliptic-curve page:

https://www.math.purdue.edu/~arapura/graph/elliptic.html

That page uses a Weierstrass-℘ parameterization and projects a complex elliptic curve into three real coordinates. Curve Explorer uses the same general projection idea, but samples the generalized Weierstrass affine equation directly as a two-sheeted cover over complex x so it works with Rank Hunter's stored a-invariants without requiring period computation.
