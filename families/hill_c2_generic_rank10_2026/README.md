# Hill C₂ generic rank-10 covers

This plugin provides two separate rational quadratic covers, numbered 10 and
13 in the source portfolio, of an elliptic K3 family with rational C₂ torsion
and nine independent sections. Each cover adds one independent section and
has verified generic rank at least 10 over `Q(U)`. Exact generic rank is not
asserted.

Pairing the covers gives a distinct rank-at-least-11 construction over a
positive-rank genus-one base. Rank Hunter exposes that construction through
the separate [`ek_z2_rank11_paired_genus1_2026`](../ek_z2_rank11_paired_genus1_2026/)
plugin. A generic lower bound does not certify every specialized fiber.

## Disclaimer

I've established that the parent K3 differs from Elkies's (2007) and Dujella–Peral (2023) examples.
I have **not** eliminated possible overlap with Elkies (2009).

## Check it

The [proof note](PROOF.md) gives the argument. The [`data/`](data/) folder
holds the exact equations, section coordinates, and height certificates.
From this directory, run the verifier with SageMath's Python:

```bash
sage -python verify.py
```

If SageMath is in a Conda environment, activate it and run `python verify.py`.
The verifier checks the parent and cover height matrices, the genus-one base,
independence of the new sections, and the torsion claim. `SHA256SUMS` records
the hashes of the packet files.
