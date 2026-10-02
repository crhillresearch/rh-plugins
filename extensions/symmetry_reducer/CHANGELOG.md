# Changelog

## 2.1.1
- Add Rank Hunter v0.8.7.1 worker aliases for `rank42.kihara_chart_search` and `rank42.mestre_chart_search`.
- Accept Fermigier chart-worker provenance where the shared Mestre planner is used.
- Preserve exact dedup/refill semantics and rank-claim boundary.


## 2.1.0

- Add transparent Feature-hook support for Kihara 2001 Möbius chart searches.
- Add transparent Feature-hook support for Mestre/Fermigier PGL2 chart searches.
- Detect both `python script.py` and `python -m module` family-worker invocations.
- Patch both shared chart planners: `build_chart_plan()` and `rank_charts()`.
- Keep `dedup` as the conservative default for validation.
- Add optional `RANK42_SYMMETRY_PLAN_MODE=refill` mode that generates farther down the family ranking until the requested number of distinct source-symmetry classes is reached where possible.
- Preserve rational-only reciprocal safety and sign-only reduction for integer/both search modes.
- Expand runtime result metadata with family, plan mode, refill counts and shortfall.
- Update Analysis workspace documentation and runtime compatibility notes.

## 2.0.3

- Fix Feature-plugin UI integration against the live v0.8.6.4 Plugins page and navigation.
