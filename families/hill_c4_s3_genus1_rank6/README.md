# Hill C4 S3 genus-one family, rank ≥6

Registered from the proof packet at [rank-ledger/c4-rank-6-s3-genus-one-family](https://github.com/crhillresearch/rank-ledger/tree/main/c4-rank-6-s3-genus-one-family). Four parent directions use the Elkies–Klagsbrun 2020 theorem; the S3 orbit supplies two additional independent directions. The genus-one base has positive rank and the fibers have exact C4 torsion.

The claim is rank at least 6 on infinitely many fibers. Exact generic rank and publication priority are not claimed.

The parameter is a nonzero integer multiple of the certified point on the
genus-one Jacobian. The family module maps it to the splitting-cover quartic
and returns an elliptic curve when the resulting fiber is smooth. The three
new cubic-orbit points and four inherited parent points are available as
exact section coordinates. The seed `2` gives the smooth witness fiber;
the base points at `0` and `7288/837` map to singular fibers and are not
validation examples.

The bundled `proof/verify.py` and its data replay the Rank Ledger argument
relative to the published Elkies–Klagsbrun rank-four parent theorem. Rank
Hunter runs that replay when validating the rank lower bound. From this
plugin directory, run `python proof/verify.py` to check the source proof
independently (Python and SymPy required).
