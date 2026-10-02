# Changelog

## 1.5.2

- Audit for Rank Hunter 0.9.2 public release.
- Add exact generic lower-bound-11 certification at t=1.
- Refresh claim-boundary and portable documentation.
- Remove stale packaging checksum drift.

## 1.2.9

- When exact rigorous non-base source fibres are recoverable for a target specialization, use only those fibres as the subgroup/discovered anchor bank for same-fibre target search.
- Keep the twelve structural Mestre base fibres as the generic rank-11 side of the chart geometry.
- Exclude ordinary dependent rediscoveries from same-fibre chart planning once rigorous exceptional anchors exist, so chart-quality ranking cannot ignore the certified directions.
- Preserve the mixed bounded seed bank for cross-fibre family scouting, where the seed geometry remains heuristic only.
- Verified on stored curve #2766 (`t=2769/2`): all 16 rigorous generators matched the current model; 5 exceptional non-base source fibres were recovered from exact persisted provenance, the 11 generic-section inverse controls passed 11/11, and subgroup target search used only those 5 exceptional fibres as the discovered anchor bank.

## 1.2.8

- Recover rigorous-basis native quartic anchors directly from exact persisted `quartic_points` provenance when the stored elliptic generator matches `mapped_point_json` exactly.
- Keep closed-form and algebraic elliptic-to-quartic inversion only as verified fallbacks for generators without a persisted source fibre.
- Reserve rigorous native anchors before filling the bounded PGL2 anchor bank with ordinary dependent discoveries, preventing the downstream height-spread planner from discarding the certified directions.
- Keep seed geometry heuristic-only: no rank evidence or independence claim is transported between specializations.

## 1.1.0

- Make the family fully standalone for Rank Hunter older releases+.
- Move the exact family, native search and PGL2 chart search into the plugin package.
- Stop dispatching to removed `rank42.mestre_*` / `rank42.families.*` modules.
- Vendor only the five pure helper functions actually needed from experimental core helpers removed in older releases.
- Preserve exact-certificate promotion and numerical-screen claim boundaries.
- Add release documentation, provenance ledger, doctor check and regression tests.

## 1.0.0

- Initial manifest/adapter wrapper used while Mestre scientific code still lived in Rank Hunter core.
