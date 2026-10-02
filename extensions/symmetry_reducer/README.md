# Symmetry Reducer v2.1.1

Rank Hunter **Feature plugin** for exact source-coordinate search-space symmetry. Requires the v0.8.6.4 functional Feature hook, or the v0.8.7.1 search-command compatibility bridge. No database-schema changes and no family-plugin edits.

## Runtime families

- **Campbell 1999 C1-C6** — A/B validated in rational PGL2 mode.
- **Mestre/Fermigier sextuple** — v2.1.1 runtime support for its shared `build_chart_plan()` PGL2 worker.
- **Kihara 2001** — v2.1.1 runtime support for its `rank_charts()` Möbius worker.

The exact source transformations are the projective-height isometries

`u`, `-u`, `1/u`, `-1/u`.

Sign is safe in every supported source mode. Reciprocal transformations are used only in unrestricted rational mode and only when the affine-infinity boundary is protected by native infinity or a known/discovered native fibre. `--include-known-fibers` disables reciprocal quotienting conservatively.

## Plan modes

### `dedup` — default

The family planner selects its ordinary top-N chart pool. Symmetry Reducer keeps the first/highest-ranked representative from each proved source-height orbit. This is the correct mode for A/B validation because it removes only duplicate work from the original plan.

### `refill` — expanded coverage

Start Rank Hunter with:

```bash
RANK42_SYMMETRY_PLAN_MODE=refill streamlit run rank42/ui.py
```

or set the environment variable on a terminal-launched Rank Hunter command. The wrapper asks the underlying planner for a larger ranked candidate pool and keeps scanning until it has the requested number of **distinct** symmetry-orbit representatives, where possible.

Refill mode intentionally changes chart coverage. It does not claim the same hit set as the unmodified top-N plan; its purpose is to buy more distinct search geometry for the same number of ratpoints launches.

## Measured pre-v2.1 audits

- Campbell C6 `t=1`: 24 -> 16 charts with 95 native fibres / 190 mapped points preserved.
- Campbell C3 `t=1`: 24 -> 13 charts; both sides had no native hits.
- Campbell C1 `t=1`: 24 -> 15 charts with 7 native fibres / 14 mapped points preserved.
- Mestre `t=1`, 64-chart census: 64 -> 35 full rational source-height classes (45.3% duplicates); sign-only gives 64 -> 48.
- Kihara `t=1`, 64-chart census: 64 -> 60 full rational source-height classes (6.25% duplicates).

The Mestre and Kihara census is an exact chart-orbit audit, **not yet a real ratpoints A/B preservation certificate**. Use `dedup` mode for those controls before enabling refill as your ordinary search policy.

## Scientific boundary

Symmetry reduction is exact search-space equivalence only. It does not prove that a mapped point is novel, independent, or rank-increasing. Numerical height screens remain heuristic scheduling tools and rigorous lower bounds change only through the project's exact certification path.
