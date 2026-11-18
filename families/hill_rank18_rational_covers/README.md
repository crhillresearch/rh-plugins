# Hill rational rank-18 covers

This Family plugin exposes two separate genus-zero families over `Q(U)`, as
variants `cover_4339` and `cover_36773`. Each is a degree-two rational base
change of the same rank-17 K3 fibration. Both have trivial rational torsion
and **verified generic rank at least 18**. Exact rank 18 is not asserted.

The complete Weierstrass coefficients, 18 rational sections per cover, and
Shioda Gram matrices are retained in the three SHA-256-pinned JSON files under
`data/`. The bundled `verify.py` is the [Rank Ledger proof replay](https://github.com/crhillresearch/rank-ledger/tree/main/generic-rank18-trivial-torsion).
Rank Hunter runs it when validating either variant's generic rank claim. It
checks the exact section identities, cover identities, height matrices,
independence, and the good-reduction trivial-torsion certificate.

Both variants tie the listed trivial-torsion lower bound 18; neither improves
that numerical bound. The rational
parameter `U` is a separate coordinate for each cover. Singular fibers return
no curve, and generic sections are only returned when their coordinates are
defined at the chosen specialization. A generic rank claim does not certify
rank 18 at every specialized fiber.

To replay the source proof:

```bash
sage -python plugins/families/hill_rank18_rational_covers/verify.py
```
