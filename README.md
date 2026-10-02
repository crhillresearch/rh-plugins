# Rank Hunter Plugins

Official installable Families, Features, and Workspaces for [Rank Hunter](https://github.com/crhillresearch/rank-hunter).

---

## Plugin types

| Type | Location | Purpose |
| --- | --- | --- |
| **Family** | [`families/`](families/) | Elliptic-curve mathematics, specialization logic, candidate generation, known sections/subgroups, and supported search adapters. |
| **Feature** | [`extensions/`](extensions/) | A focused hook into an existing Rank Hunter workflow without its own page. |
| **Workspace** | [`extensions/`](extensions/) | A self-contained research page shown under **Workspaces** when enabled. |

Every installable plugin is its own directory with a `plugin.json` manifest. Rank Hunter recognizes manifest types `family`, `feature`, and `extension` (shown in the UI as a Workspace).

**RELEASE policy for new Families:** Candidate Generation alone is not release-complete. New Family plugins must also provide working **Family Search** and **Target Search** adapters with focused tests. Older audited plugins may expose a narrower capability set where their manifest says so.

## Published Families

| Family | Version | Purpose |
| --- | ---: | --- |
| [Campbell C1-C6](families/campbell1999_rank13/) | 3.0.3 | Six Campbell rank-13 branches with exact variants and deep search support. |
| [DMT Triad Family](families/dmt_triad_rank4/) | 0.1.3 | Six Piezas-sextuple triads with full rational 2-torsion and four generic sections. |
| [Elkies Rank-17 K3](families/elkies_rank17_2026/) | 1.3.1 | Published rank-17 K3 record-hunt family with all 17 generic sections. |
| [Elkies Rank-18 First Cover](families/elkies_rank18_2026/) | 0.1.1 | First quadratic base change of the Elkies rank-17 K3 with an exact 18th section. |
| [Elkies X1092 - Published MW17](families/elkies_x1092_rank17/) | 1.2.0 | X1092 K3 fibration with 17 exact generic sections and fast Nagao screening. |
| [Elkies-Klagsbrun Z/2 K3](families/elkies_klagsbrun_z2_rank9_2020/) | 1.2.4 | Z/2-torsion K3 family of generic rank 9 with a proven rank-20 specialization. |
| [Fermigier-Mestre K3](families/fermigier_rank12_exact/) | 1.1.0 | One-parameter K3 reconstruction with 12 exact generic sections. |
| [Fibonacci Triples](families/fibonacci_triples/) | 0.1.3 | Odd/even elliptic families induced by Fibonacci Diophantine triples. |
| [Kihara (2001)](families/kihara_rank14/) | 1.2.0 | Published generic-rank-at-least-14 family with 14 exact sections. |
| [Kloosterman Rank-15 K3](families/kloosterman_rank15/) | 1.1.0 | Explicit K3 surface proved in the literature to have Mordell-Weil rank 15. |
| [Mazur Torsion Families](families/mazur_torsion_families/) | 0.1.5 | Prescribed-torsion candidate lanes covering all 15 rational torsion groups allowed over Q. |
| [Mestre/Fermigier Sextuple](families/mestre_sextuple_rank11/) | 1.5.2 | Generic-rank-at-least-11 Mestre sextuple family with quartic/PGL2 deep search. |
| [Dujella-Peral Z/4 Rank 6](families/dujella_peral_z4_rank6/) | 0.1.1 | Published Z/4 family with exact generic rank 6 and six reconstructed generators. |
| [Dujella-Peral-Tadic Z/6 Rank 3 Families](families/dujella_peral_tadic_z6_rank3/) | 0.1.0 | Six explicit Z/6 rank-3 variants from the definitive 2016 treatment. |
| [Z/8 Rank-2 Families](families/z8_rank2_families/) | 0.1.0 | Seven pairwise non-isomorphic Z/8 families of exact generic rank 2. |
| [Z/2 x Z/6 Rank-2 Families](families/c2xc6_rank2_families/) | 0.1.0 | Five pairwise non-isomorphic Z/2 x Z/6 families of exact generic rank 2. |
| [Dujella-Peral Z/2 x Z/4 Diophantine Triple Rank 4](families/c2xc4_diophantine_rank4/) | 0.1.0 | Exact generic-rank-4 prescribed-torsion family induced by Diophantine triples. |
| [Dujella-Peral Diophantine Triple Rank 6](families/diophantine_triple_rank6/) | 0.1.0 | Fully explicit C2 x C2 Diophantine-triple family of exact generic rank 6. |
| [Dujella-Peral Rational Diophantine Triple Rank >=7](families/rational_diophantine_rank7/) | 0.1.0 | Genus-1-base infinite C2 x C2 family with verified generic lower bound 7. |
| [Nagao j=1728 Rank >=4 Twist Family](families/nagao_j1728_rank4/) | 0.1.0 | Nagao j=1728 family with four independent generic sections. |

Each Family README/provenance file states its exact scientific claim boundary. A literature theorem, a verified generic lower bound, a specialized exact rank, and a heuristic search score are not interchangeable.

## Published Features and Workspaces

| Plugin | Type | Version | Purpose |
| --- | --- | ---: | --- |
| [Curve Explorer](extensions/curve_explorer/) | Workspace | 0.4.8 | Interactive real-locus explorer with exact P/Q -> R -> -R playback for stored curves. |
| [Leaderboard Compare](extensions/leaderboard_compare/) | Workspace | 0.2.1 | Compare Rank Hunter curves with synchronized high-rank leaderboard data and torsion filters. |
| [Symmetry Reducer](extensions/symmetry_reducer/) | Feature | 2.1.1 | Exact search-space symmetry reduction for supported Campbell, Kihara, and Mestre/Fermigier searches. |

## Validation and provenance

Published plugins are expected to preserve source/provenance, distinguish heuristic signals from exact or rigorous evidence, keep plugin-local scientific runners write-free where core owns persistence, and pass focused tests plus current-core manifest/adapter validation before publication.

If a plugin produces unexpected mathematics, report the plugin name/version, Rank Hunter version, curve or parameter, and the failing command/log.

## Plugin author guides

- [Writing a Family plugin](docs/FAMILY_PLUGINS.md)
- [Writing a Feature plugin](docs/FEATURE_PLUGINS.md)
- [Writing a Workspace plugin](docs/WORKSPACE_PLUGINS.md)
- [Documentation index](docs/README.md)

For Rank Hunter itself, see the [Rank Hunter repository](https://github.com/crhillresearch/rank-hunter).
