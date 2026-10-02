# Fibonacci Triples · v0.1.3

Rank Hunter Family plugin for the two one-parameter elliptic families attached to Fibonacci Diophantine triples in Andrej Dujella, *Ranks and integer points on elliptic curves induced by Fibonacci triples*.

Release-audited for Rank Hunter **0.9.2**.

## Published source

- arXiv: https://arxiv.org/abs/2609.01789
- DOI: 10.48550/arXiv.2609.01789
- submitted: 1 September 2026
- generic-rank result: Theorem 5.1
- odd-index independence: Proposition 3.3
- rational parameterizations: equations (14) and (15)

The paper studies

```text
E_k: y^2 = (F_{2k}x+1)(F_{2k+2}x+1)(F_{2k+4}x+1).
```

For odd `k >= 3`, it gives the second rational point

```text
Q_k = (
  -F_{k-1}/(L_k F_{k+1} F_{k+2}),
   F_{2k+1}/(L_k F_{k+1} F_{k+2})
)
```

and proves `P_k=(0,1)` and `Q_k` independent.

## Two one-parameter families

Dujella separates the parity classes through the conics
`L^2-5F^2 = ±4`.

### Odd family E-

Equation (14):

```text
f   = (T^2 - 2T + 5)/(T^2 - 5)
ell = -(T^2 - 10T + 5)/(T^2 - 5)
```

The paper proves exact generic rank **2**.

Rank Hunter bundles the two explicit generic sections corresponding to `P` and `Q`.

### Even family E+

Equation (15):

```text
f   = -4T/(T^2 - 5)
ell = -2(T^2 + 5)/(T^2 - 5)
```

The paper proves exact generic rank **1**.

Rank Hunter bundles the standard section `P`.

For both families:

```text
u    = (ell + f)/2
v    = (ell + 3f)/2
ell1 = (ell + 5f)/2
ell2 = (3ell + 5f)/2

a = f*ell
b = u*ell1
c = v*ell2
```

and after

```text
X = abc*x
Y = abc*y
```

the curve is

```text
Y^2 = (X+bc)(X+ac)(X+ab).
```

## Rank claim boundary

The paper proves the exact generic ranks:

- odd E-: rank **2**;
- even E+: rank **1**.

The Rank Hunter manifest preserves those exact values as literature provenance.

Operationally, Rank Hunter verifies the explicit-section lower bounds independently:

- odd: `verified_generic_rank_lower = 2`;
- even: `verified_generic_rank_lower = 1`;
- both use `generic_rank_claim_state = generic_lower_bound_verified`.

The odd validator exact-certifies the two explicit sections as independent at good control `T=3`.

The even validator exact-certifies the explicit section as non-torsion at `T=20/9`.

These specialization certificates prove the corresponding generic **lower bounds**. They do not re-run Dujella's injective-specialization proof of the exact generic upper bounds.

For ordinary rational specializations, Rank Hunter still promotes rigorous rank lower bounds only from exact specialized point-independence evidence.

## Published controls

The paper's generic-rank proof uses:

- odd: `T=85/38`, corresponding to `k=17`;
- even: `T=20/9`, corresponding to `k=12`.

The plugin also keeps simple exact positive controls:

- `T=3` corresponds to `k=3`;
- `T=5/2` corresponds to `k=5`;
- `Q_3=(-1/60,13/60)`;
- `Q_5=(-3/1144,89/1144)`.

## Fibonacci-index chart

Actual Fibonacci fibers are embedded in the ambient rational `T)-families by:

- odd `k >= 3`: `T=(L_k-1)/(F_k-1)`;
- even `k`: `T=5F_k/(L_k+2)`.

The exceptional `k=1` odd point is not represented by the affine odd `T)-chart used here.

## Search behavior

The Family supports:

- candidate generation;
- Family Search;
- Target Search;
- known generic sections;
- free search.

Family Search delegates arithmetic screening to current core `rank42.auto_analyze` using PARI-first quick screening while preserving the explicit family sections and exact generic certificate.

Target Search reconstructs the exact stored rational family parameter into a one-row candidate and reuses the same family-aware core analyzer with `--force`.

The plugin does not claim a family-specific quartic/PGL2 search backend.

## Heuristic rank distribution

The paper combines forced-rank baselines, parity, root numbers, and minimalist heuristics to propose asymptotic densities

```text
rank 1: 1/4
rank 2: 1/2
rank 3: 1/4
rank >=4: density 0
```

The plugin exposes that as heuristic helper logic only. It never writes rigorous rank evidence from the heuristic.

## Validation

Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout, then from the plugin repository run:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/fibonacci_triples/tests
```

The release gate checks the paper formulas, Fibonacci-index controls, exact sections, both generic lower-bound certificates, current-core plugin validation, adapter command contracts, and Target bridge behavior.

## Version history

### v0.1.3

Rank Hunter 0.9.2 release audit. Refreshes Dujella provenance, distinguishes the paper's exact generic-rank theorem from Rank Hunter's operational lower-bound certificates, updates certificate provenance, and adds current-core release validation.

### v0.1.2

Added manifest-owned search presets/options, Family-aware Target Search, PARI-first screening, and exact generic lower-bound callbacks.
