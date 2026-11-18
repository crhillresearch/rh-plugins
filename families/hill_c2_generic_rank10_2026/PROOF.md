# Proof notes: an infinite C2-torsion family of rank at least 11

## The statement

Let `E_t` be the Elkies–Klagsbrun C2 elliptic K3 family in
`data/source-family-u11_5.json`. There is a smooth genus-one curve `C` with
a degree-four map to the `t`-line, obtained by adjoining square roots of two
quadratic branch polynomials `q10(t)` and `q13(t)`. Over `Q(C)`, the pulled-
back elliptic curve has eleven independent rational sections and rational
torsion exactly `C2`. The curve `C` has infinitely many rational points, and
the elliptic curve is non-isotrivial. Therefore infinitely many rational
specializations have rank at least 11.

This is a lower-bound theorem. The rank-11 statement is over `Q(C)`, not the
original `Q(t)` family. The original one-parameter family has rank at least
9. No exact rank claim is made for every fiber.

## 1. The common rank-9 parent

The parent model and its nine section coordinates are in
`data/parent-rank9.json`. `verify.py` reconstructs its elliptic curve over
`Q(U)`, checks all nine sections, factors the discriminant, verifies the
I1/I2 fiber types, and recomputes the Shioda height matrix. At every I2
fiber it checks `c4` is a unit and subtracts `1/2` exactly when a section
meets the nonidentity component. The resulting Gram matrix is positive
definite with determinant `115/16`; hence the nine sections are independent.

The source-family chart in `data/source-family-u11_5.json` displays the
rational 2-torsion section. At the smooth fiber `t=-13/30`, Sage's exact
rational torsion computation gives invariants `[2]`. Specialization of
rational torsion at a smooth fiber is injective, so the generic rational
torsion is exactly `C2`.

## 2. The two quadratic covers and their common genus-one base

`data/quadratic-cover-portfolio.json` records the quadratic-section
portfolio. Its entries 10 and 13 give squarefree quadratic polynomials
`q10,q13`. The verifier checks that they are coprime, so their square classes
are independent in `Q(t)^*/Q(t)^{*2}`. Their compositum has Galois group
`(Z/2Z)^2`.

The exact conic parametrization of the first cover is recorded in
`data/paired-cover-base.json` as polynomials `N(s), D(s), W(s)`. The verifier
checks

```
q10(N/D) = (W/D)^2,
q13(N/D) D^2 = F(s),
```

where `F` is the recorded squarefree quartic. Thus the compositum is
birational to `w^2=F(s)`, a genus-one curve. Since `F(0)` is a rational
square, this curve has a rational point.

The associated Jacobian coefficients and rational point are also recorded.
The verifier reconstructs the quartic-to-Jacobian map and checks its exact
identity. It replays the Jacobian group orders at the listed good primes and
uses the reduction bounds to show that the recorded point is not torsion.
Thus `C(Q)` is infinite.

## 3. Exact rank 10 on each cover

For each index `i=10,13`, `data/cover-i/model.json` gives the exact
degree-two base change, Weierstrass model, and ten sections. The first nine
are the parent sections; the last is the new section. The matching
`shioda-certificate.json` records the correction-aware height Gram matrix.

The verifier does not trust the stored matrix: it rebuilds the elliptic
curve and all ten points, confirms the base-change identities, factors the
discriminant, checks the multiplicative I2 fibers, recomputes every Shioda
pairing with the component corrections, and compares with the receipt. Each
Gram matrix is positive definite with determinant `11040`, and the leading
nine-by-nine block is twice the parent Gram matrix. The Schur complement of
the parent block is `3`.

The deck involution of each degree-two cover fixes all nine parent sections.
The verifier replays the involution on section coordinates. It sends the new
section to a distinct conjugate, and the exact corrected height of the
difference is `12` on each cover. Thus each cover contributes one
nonzero anti-invariant direction.

## 4. Why the two new sections are independent together

The cover involutions extend to the compositum by fixing the other square
root. Suppose there were an integer relation among the nine parent sections
and the two new sections. Applying the first involution minus the identity
kills the parent sections and the second new section, leaving a multiple of
the first anti-invariant. Its positive height forces that coefficient to
vanish. The second involution similarly kills the second coefficient. The
remaining relation is among the nine parent sections, whose Gram matrix is
positive definite. All coefficients vanish. Therefore the eleven sections
are independent over `Q(C)`.

## 5. Infinitely many rank-at-least-11 fibers

The auxiliary Jacobian point is nontorsion, so the genus-one parameter curve
has infinitely many rational points. The verifier checks the `j`-invariant
of `E_t` is nonconstant. Silverman's specialization theorem for an elliptic
surface over a curve then preserves the eleven-section subgroup for all but
finitely many rational base points. Hence infinitely many rational fibers
have rank at least 11.

## Reproducibility

Run `sage -python verify.py` from this folder. The verifier reads only the
JSON inputs in `data/` and checks the exact algebraic identities and height
calculations above. `SHA256SUMS` lets you detect accidental changes to the
packet.
