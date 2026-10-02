# Campbell C1-C6 · Rank-13 family plugin v3.0.3

This Rank Hunter Family plugin exposes the six one-parameter rank-13 families in Garikai Campbell's 1999 dissertation as variants `c1` through `c6`.

Each variant has its own exact JSON family model with 13 displayed rational sections. The variant is stored separately from the rational specialization parameter, so the six Campbell landscapes remain distinct while appearing as one installed Family.

## Published source

Garikai Campbell, *Finding Elliptic Curves and Families of Elliptic Curves over Q of Large Rank*, PhD dissertation, Rutgers University, 1999, Chapter 3 §3.3.2.

Source PDF:

https://ctnt-summer.math.uconn.edu/wp-content/uploads/sites/1632/2020/06/Campbell-Finding-elliptic-curves-and-families-of-elliptic-curves-over-Q-of-large-rank.pdf

Campbell's §3.3.2 table gives these six sextuples and additional point x-coordinates:

| Variant | Sextuple A | Additional x |
| --- | --- | --- |
| C1 | `[0, 87, 164, 264, 375, 452]` | `(7/31)t + 10848/31` |
| C2 | `[0, 55, 146, 255, 260, 346]` | `(-7/27)t + 6920/27` |
| C3 | `[0, 355, 602, 910, 1580, 1827]` | `(19/89)t + 127890/89` |
| C4 | `[0, 97, 104, 129, 500, 532]` | `(1/23)t + 9804/23` |
| C5 | `[0, 42, 47, 82, 152, 175]` | `(1/21)t + 410/3` |
| C6 | `[0, 37, 62, 110, 180, 205]` | `(7/23)t + 1271/23` |

Campbell states that after parameterizing the relevant quartic so that it has two rational points at infinity, the remaining 13 displayed points are linearly independent.

## Rank Hunter claim boundary

The literature rank-13 statement is represented as:

- `historical_generic_rank_lower = 13`
- `generic_rank_claim_state = historical_record`

It is deliberately **not** treated as an automatic rigorous lower bound for every specialization. Rank Hunter promotes a specialized curve's lower bound only after exact specialized point verification and independence certification.

## Search support

The plugin provides:

- candidate generation;
- Family Search;
- Target Search;
- native quartic search;
- PGL2 chart search;
- known-subgroup scheduling;
- free-search chart generation.

The native and PGL2 workers receive the selected Campbell variant from Rank Hunter automatically.

## Compatibility

Release-audited against the Rank Hunter **0.9.2** development line. Install under the Families plugin collection, restart Rank Hunter, and validate the Family from Plugins before using it for searches.

## Version history

### v3.0.3

Release audit for Rank Hunter 0.9.2. Adds explicit dissertation provenance, verifies the six published sextuples/additional x-coordinates against Campbell §3.3.2, removes stale 0.8.x compatibility wording, and keeps the generic-rank claim historical rather than operational.

### v3.0.2

Moved shared height-stage and affine-key helpers to `rank42.general_hunt_core`; kept Campbell-specific subgroup scheduling plugin-local. Converted the literature rank-13 claim to historical claim metadata so specialized lower bounds still require exact Rank Hunter certification.

### v3.0.1

Fixed variant-aware candidate identity handling for the consolidated six-variant plugin. Legacy per-branch Campbell plugin IDs remain accepted for matching historical candidate provenance.
