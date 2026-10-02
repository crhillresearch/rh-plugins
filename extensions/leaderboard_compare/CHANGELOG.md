# Changelog

## 0.2.1

- Add rational torsion-group filtering across Rank Hunter and ICARM rows.
- Read Rank Hunter's stored exact `torsion_label` when the torsion schema is available.
- Read ICARM's source-provided torsion invariant factors from synchronized `raw_json`.
- Keep unknown torsion explicit rather than recomputing or guessing it.
- Show torsion in plot tooltips, best-record captions, and the plotted-row table.
- Preserve all existing leaderboard metric/frontier semantics and Light/Dark theme behavior.

## 0.2.0

- Rename **ICARM Charts** to **Leaderboard Compare** throughout the plugin identity.
- Rename the install folder from `icarm_charts` to `leaderboard_compare`.
- Move the v0.1.1 theme shim into the real extension entrypoint and remove the legacy wrapper split.
- Replace the chart/table fixed dark palette with semantic Rank Hunter `rh-*` theme tokens.
- Add plugin-scoped Light/Dark token styling for radio, slider, selectbox, multiselect, and checkbox controls.
- Preserve ICARM as the external comparison data source and preserve all leaderboard/evidence semantics.

## 0.1.1

- Add theme-aware compatibility styling for the ICARM Charts workspace.
