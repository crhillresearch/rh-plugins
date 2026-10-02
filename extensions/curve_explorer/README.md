# Curve Explorer v0.4.8

Interactive Rank Hunter extension for inspecting the real locus of a stored elliptic curve while keeping rational-point arithmetic exact over **Q**.

## v0.4.8 highlights

- **Construct** playback now works for any selected stored P/Q pair, not only pairs inside the bounded precomputed cache.
- Cached pairs still use Python-precomputed exact constructions for speed.
- Uncached pairs are computed exactly in the embedded explorer with BigInt rational arithmetic using the same generalized Weierstrass secant/tangent formulas as the Python backend.

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
