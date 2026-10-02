# Mestre/Fermigier Sextuple · v1.5.2 Rank-11 Family

Standalone Rank Hunter family plugin for the fixed Mestre/Fermigier sextuple

```text
[348, -600, -216, 492, 876, -900]
```

and its one-parameter genus-one quartic construction.

## What is included

- exact normalized native quartic and square-completion construction;
- twelve exact rational base fibres and eleven non-origin section points;
- exact `t <-> -t` native-quartic symmetry and parameter-orbit canonicalization;
- native quartic `ratpoints` search;
- exact PGL2/Möbius chart search using base, subgroup-derived, and free charts;
- exact inverse mapping of every chart hit to the native quartic;
- exact mapping to `E(Q)`;
- numerical Néron-Tate novelty ordering;
- exact quadratic-character certificate path before rigorous lower-bound promotion;
- Rank Hunter family-search and target-search adapters.

The plugin contains all **Mestre-family-specific** mathematics. Generic Rank Hunter DB, `ratpoints`, exact-certificate, height-worker, lattice-store, Möbius and timeout infrastructure remains in core.

### Deep target scheduling

Target searches keep the same exact PGL2 mathematics but schedule expensive rational work more carefully. At configured high heights, denominator space is split into persistent bands, so completed bands are reused on later runs. Record Hunt first runs the cheaper stages across the full chart bank, ranks charts by exact non-base native fibres recovered from those stages, and promotes only the most productive charts to the deepest rational height. Each band has its own timeout/circuit breaker; a hard band cannot pin every remaining chart indefinitely. These are search-scheduling optimizations only and do not alter the proof boundary.

### Second-generation fiber expansion

Fiber Expansion is a reusable target strategy for already-interesting Mestre specializations. It keeps structural/rigorous native fibres as the certified geometry set and separately ranks previously discovered exact mapped fibres as geometry-only anchors. The exploratory pool favors a balance of recent discoveries and large denominators, builds exact mixed PGL2 charts from certified + exploratory anchors, and can include fully exploratory charts for coordinate diversity. Exploratory anchors never enter the Mordell-Weil basis and never count as rank evidence. Deep promotion is scored by genuinely new native x-fibres first discovered during the current run, and the job summary records which denominator bands produced those new fibres.

## Scientific claim boundary

`generic_rank = 11` records the family lower-bound target and the plugin exposes eleven exact non-origin section points. Numerical height residuals are only search screens. Specialization lower bounds are promoted only through Rank Hunter's exact certificate path; the plugin does not equate a section list, chart hit, or numerical novelty residual with a proof of rank growth.

## Reference

J.-F. Mestre, *Courbes elliptiques de rang >= 11 sur Q(t)*, C. R. Acad. Sci. Paris Ser. I Math. 313 (1991), 139-142.

The plugin's fixed sextuple and public-control metadata are recorded in `family.py` / `plugin.json`.

## Rank Hunter compatibility

- Rank Hunter: **0.9.2**
- SageMath Python is required for scientific execution.
- `ratpoints` is required for point search.

## Install

Put or symlink this directory directly below Rank Hunter's `plugins/` directory:

```bash
cd ~/rank-hunter/plugins
ln -sfn ~/rank-hunter-plugins/mestre_sextuple_rank11 mestre_sextuple_rank11
```

If `~/rank-hunter/plugins` already points at `~/rank-hunter-plugins`, no extra link is required.

## Validate

```bash
cd ~/rank-hunter
sage -python -m rank42.plugin_validate --plugin mestre_sextuple_rank11
sage -python families/mestre_sextuple_rank11/doctor.py
sage -python -m pytest -q families/mestre_sextuple_rank11/tests
```

## Files

```text
plugin.json        Rank Hunter manifest
family.py          exact Mestre sextuple mathematics
search_adapter.py  thin Rank Hunter command adapter
native_search.py   native-quartic search/certificate worker
chart_search.py    PGL2/Möbius chart worker
search_helpers.py  five small pure numerical/parser helpers needed by workers
doctor.py          standalone release sanity check
tests/             regression tests
```

`search_helpers.py` deliberately contains only the helper functions used by this family. They came from experimental generic modules that were removed from core in older releases; carrying the five required pure functions here avoids reintroducing those old modules into Rank Hunter core.
