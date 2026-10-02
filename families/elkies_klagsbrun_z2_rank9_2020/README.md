# Elkies–Klagsbrun Z/2 K3 · v1.2.4

Rank Hunter Family plugin for the rational-2-torsion elliptic K3 family in Noam D. Elkies and Zev Klagsbrun, *New Rank Records For Elliptic Curves Having Rational Torsion*.

Release-audited for Rank Hunter **0.9.2**.

## Published source

- arXiv: https://arxiv.org/abs/2003.00077
- DOI: 10.2140/obs.2020.4.233
- Open Book Series 4 (2020), 233–250
- family construction/search discussion: §9
- nine generic generators: Appendix A
- rank-20 specialization: Appendix B.2

The family is

```text
y^2 = x^3 + 2 A(t,u) x^2 + B(t,u) x
```

with `B = ∏ B_i`.

For admissible rational `u` satisfying `5-u^2` square and `u != ±1, ±2`, Elkies–Klagsbrun state

```text
E_u(Q(t)) = Z/2Z × Z^9.
```

The four native Rank Hunter variants are the published/search values

```text
u = 11/5
u = 2/5
u = 2/13
u = 22/13
```

and every JSON family carries the visible rational 2-torsion point `(0,0)` plus nine exact generic sections.

## Generic-rank claim boundary

The manifest keeps:

```text
generic_rank = 9
historical_generic_rank_lower = 9
generic_rank_claim_state = sections_verified
```

Rank Hunter exact-symbolically verifies all nine bundled sections over `Q(t)`, but this plugin deliberately does not synthesize a stronger new-style `verified_generic_rank_lower` certificate from metadata alone.

For a rational specialization, the nine specialized sections are mapped exactly to the stored curve/minimal model and Rank Hunter's exact independence certificate must succeed before the rigorous specialization lower bound is raised.

Nagao scores remain heuristic. A `ratpoints` hit is an exact rational point after membership verification, but it is not automatically a new independent direction.

## Native variants and published chart

Native branches:

- `u11_5` — primary branch; published exact-rank-20 control at native `t=-721141/2026305`;
- `u2_5` — published rank-19 control at `t=11860/97527`;
- `u2_13` — published contrast branch;
- `u22_13` — published contrast branch.

The fifth variant, `u11_5_published_chart_search`, is the exact transformed search representation for the paper's Möbius search chart.

Rank Hunter's chart matrix is

```text
[-1, 2, 1, -6]
```

so

```text
native_t = (2 - chart_t)/(chart_t - 6).
```

Core PGL2 handling stores chart/native parameters separately and deduplicates scientific identity by the canonical native fiber.

## Rank-20 control and printed-chart discrepancy

The paper reports the rank-20 fiber as:

```text
transformed chart parameter: -68559/32629
native parameter:            -721141/2026305
```

Those two values do **not** satisfy the paper's stated Möbius map.

Exact inversion of the native rank-20 parameter gives

```text
-68559/326291
```

which does map exactly to `-721141/2026305`.

Rank Hunter therefore stores all three pieces of provenance:

- the source-printed chart parameter;
- the published native parameter;
- the exact map-consistent corrected chart parameter used operationally.

The paper's rank-19 chart/native pair
`100782/104143 -> -26876/131019`
does satisfy the same map exactly.

## Unconditional rank-20 control

At `u=11/5`, native `t=-721141/2026305`, the paper gives a minimal model and 20 generator x-coordinates and states that the curve has exact rank 20 unconditionally.

The release self-check verifies:

- the plugin specialization is isomorphic to the published minimal model;
- all 20 published generator x-coordinates lift on that model;
- the nine generic sections specialize exactly.

This published exact-rank record is provenance/control data. Rank Hunter does not hard-code `exact_rank=20` merely because a local parameter matches the paper.

## Search integration

Family Search delegates to core `rank42.auto_analyze` and uses the current PARI/mwrank screening path.

Target Search delegates to `rank42.fixed_curve_search`, starting from rigorous witnesses already stored in Rank Hunter's point/evidence ledger.

The search adapter was audited against Rank Hunter 0.9.2; every CLI option it emits is still owned by the corresponding core runner.

## Validation

Focused release gate. Set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/elkies_klagsbrun_z2_rank9_2020/tests
```

The gate covers:

- all five symbolic family/chart representations;
- visible rational 2-torsion;
- exact published Möbius chart mapping;
- rank-20 published-model/generator controls;
- current-core plugin validation and adapter contracts.

## Version history

### v1.2.4

Rank Hunter 0.9.2 release audit. Refreshes source/claim provenance, documents the rank-20 chart discrepancy explicitly, removes a local absolute symlink artifact, and adds a current-core release validation gate.

### v1.2.3

PARI-first/core-chart integration with native/chart provenance, exact specialization certification, and unified Target Search.
