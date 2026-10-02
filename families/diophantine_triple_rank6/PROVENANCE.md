# Provenance — Dujella–Peral Diophantine Triple Rank 6

Primary authority: Dujella–Peral, *Elliptic curves induced by Diophantine
triples*, RACSAM 113 (2019), §§2.3–2.6.

The release family is the fully explicit §2.5 construction. The paper prints
its cleared A(v), factored B(v), six independent x-coordinates and a
Diophantine quadruple. Specialization v=5 satisfies the Gusić–Tadić injectivity
criterion and proves exact generic rank 6 with torsion C2 × C2.

The original arXiv/published formula has
x6 = +9(-27+13v^2)^2(-13+27v^2)^2(9+8018v^2+9v^4)(31-258v^2+31v^4).
A later survey prints -9. Exact rational substitution at v=5 shows +9 gives a
rational point on the published curve and -9 does not, so the plugin uses +9.

Section 2.6 lists three further base changes a1(v), a2(v), a3(v) of the rank-4
parent and states that they also give rank-6 curves. It explicitly says the
paper presents details for one case and only quotes the specializations in the
other three. Because the two additional independent section formulas are not
provided, these are provenance/research leads rather than operational release
variants.

The maintained Dujella torsion table, checked 2026-10-02, gives best known
lower bound 15 for C2 × C2, so record search targets 16.

The paper's exact generic-rank theorem remains theorem provenance; Rank Hunter
operationally reproduces the six-direction lower bound at v=5.
