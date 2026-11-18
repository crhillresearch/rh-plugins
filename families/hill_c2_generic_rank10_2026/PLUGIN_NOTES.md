# Hill C₂ generic rank ≥10 covers

This Family plugin provides two separate rationally parametrized elliptic families over `Q(U)`, `cover10` and `cover13`. Each has ten independent generic sections and rational torsion exactly `C2`. These are generic lower bounds; exact generic ranks are not asserted.

Each cover is a degree-two rational base change of the Elkies–Klagsbrun rank-9 family at `t = 11/5`. The ten section coordinates, expanded Weierstrass coefficients, and corrected Shioda certificates are imported from the Rank Ledger packet at commit `1c63174ed3b85002b229c8b5a08b53466077886a` without modifying the mathematical JSON inputs.

The exact verifier replays the parent and cover Shioda matrices, base-change identities, corrected I₂ contributions, and torsion specialization. Its separate rank-11 conclusion concerns the combined genus-one base; this plugin imports only the two independent rank-at-least-10 families over `Q(U)`.

Run `sage -python verify.py` from this directory. The plugin validation parameter is `U = 0`. The operational torsion section is obtained by transforming the visible `(0,0)` from the native model into short Weierstrass coordinates; it is generally not `(0,0)` on the plugin's short model.
