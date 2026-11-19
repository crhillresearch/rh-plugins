# Rank Hunter Plugins

Official installable Families, Features, and Workspaces for [Rank Hunter](https://github.com/crhillresearch/rank-hunter).

---

## Plugin types

| Type | Location | Description |
| --- | --- | --- |
| **Family** | [`families/`](families/) | Elliptic-curve mathematics, specialization logic, candidate generation, known sections/subgroups, and supported search adapters. |
| **Feature** | [`extensions/`](extensions/) | A focused hook into an existing Rank Hunter workflow without its own page. |
| **Workspace** | [`extensions/`](extensions/) | A self-contained research page shown under **Workspaces** when enabled. |

Every installable plugin is its own directory with a `plugin.json` manifest. Rank Hunter recognizes manifest types `family`, `feature`, and `extension` (shown in the UI as a Workspace).

## Published Families

| Family | Version | Description |
| --- | ---: | --- |
| **Trivial** | | |
| [Hill Rank-19 K3](families/hill_rank19_k3/) | 0.4.2 | Verified generic rank at least 19 over a positive-rank genus-one base formed from two quadratic K3 covers; individual fibers require exact rank evidence. |
| [Elkies Rank-18 First Cover](families/elkies_rank18_2026/) | 0.1.1 | First quadratic base change of the Elkies rank-17 K3 with an exact 18th section. |
| [Hill Rational Rank-18 Covers](families/hill_rank18_rational_covers/) | 0.1.0 | Two separate rational quadratic covers, each with verified generic rank at least 18 over Q(U) and trivial torsion. |
| [Elkies Rank-17 K3](families/elkies_rank17_2026/) | 1.3.1 | Published rank-17 K3 record-hunt family with all 17 generic sections. |
| [Elkies X1092 - Published MW17](families/elkies_x1092_rank17/) | 1.3.0 | X1092 K3 fibration with 17 exact generic sections, fast Nagao screening, and subgroup-aware Family/Target search. |
| [Kloosterman Rank-15 K3](families/kloosterman_rank15/) | 1.1.0 | Explicit K3 surface proved in the literature to have Mordell-Weil rank 15. |
| [Kihara (2001)](families/kihara_rank14/) | 1.2.0 | Published generic-rank-at-least-14 family with 14 exact sections. |
| [Campbell C1-C6](families/campbell1999_rank13/) | 3.0.3 | Six Campbell rank-13 branches with exact variants and deep search support. |
| [Fermigier-Mestre K3](families/fermigier_rank12_exact/) | 1.1.0 | One-parameter K3 reconstruction with 12 exact generic sections. |
| [Mestre/Fermigier Sextuple](families/mestre_sextuple_rank11/) | 1.5.2 | Generic-rank-at-least-11 Mestre sextuple family with quartic/PGL2 deep search. |
| **ℤ/2ℤ** | | |
| [Hill C2 Rank ≥11 Genus-One-Base Family](families/ek_z2_rank11_paired_genus1_2026/) | 0.1.0 | Paired C2 covers with a verified rank-at-least-11 lower bound over a positive-rank genus-one base. |
| [Hill C₂ Generic Rank-10 Covers](families/hill_c2_generic_rank10_2026/) | 0.1.0 | Two separate rational C2 covers, each with ten independent generic sections over Q(U). |
| [Elkies-Klagsbrun Z/2 K3](families/elkies_klagsbrun_z2_rank9_2020/) | 1.2.4 | Z/2-torsion K3 family of generic rank 9 with a proven rank-20 specialization. |
| [Nagao j=1728 Rank >=4 Twist Family](families/nagao_j1728_rank4/) | 0.1.0 | Nagao j=1728 family with four independent generic sections. |
| **ℤ/4ℤ** | | |
| [Dujella–Peral E2 · C4 Rank 6](families/dujella_peral_joint_2026_e2/) | 0.1.0 | New inequivalent rank-6 C4 family from the joint quadratic base-change construction (2026). |
| [Dujella-Peral Z/4 Rank 6](families/dujella_peral_z4_rank6/) | 0.1.1 | Published Z/4 family with exact generic rank 6 and six reconstructed generators. |
| [Hill · C4 Rank ≥6 · S3 Genus-One Base](families/hill_c4_s3_genus1_rank6/) | 0.1.0 | Infinite C4 family with a verified rank-at-least-6 lower bound over a positive-rank genus-one base. |
| **ℤ/6ℤ** | | |
| [Jaswal C6 Generic Rank 4](families/jaswal_c6_rank4/) | 0.1.0 | Jaswal's rational C6 family of exact generic rank 4. |
| [Dujella-Peral-Tadic Z/6 Rank 3 Families](families/dujella_peral_tadic_z6_rank3/) | 0.1.0 | Six explicit Z/6 rank-3 variants from the definitive 2016 treatment. |
| **ℤ/8ℤ** | | |
| [Z/8 Rank-2 Families](families/z8_rank2_families/) | 0.1.0 | Seven pairwise non-isomorphic Z/8 families of exact generic rank 2. |
| **ℤ/2ℤ × ℤ/2ℤ** | | |
| [Dujella-Peral Rational Diophantine Triple Rank >=7](families/rational_diophantine_rank7/) | 0.1.0 | Genus-1-base infinite C2 x C2 family with verified generic lower bound 7. |
| [Dujella-Peral Diophantine Triple Rank 6](families/diophantine_triple_rank6/) | 0.1.0 | Fully explicit C2 x C2 Diophantine-triple family of exact generic rank 6. |
| [DMT Triad Family](families/dmt_triad_rank4/) | 0.1.3 | Six Piezas-sextuple triads with full rational 2-torsion and four generic sections. |
| [Fibonacci Triples](families/fibonacci_triples/) | 0.1.3 | Odd/even elliptic families induced by Fibonacci Diophantine triples. |
| **ℤ/2ℤ × ℤ/4ℤ** | | |
| [Jaswal C2 × C4 Genus-One Rank 6](families/jaswal_c2xc4_rank6/) | 0.1.0 | First genus-one family in Jaswal's rank-at-least-6 C2 × C4 paper. |
| [Dujella-Peral Z/2 x Z/4 Diophantine Triple Rank 4](families/c2xc4_diophantine_rank4/) | 0.1.0 | Exact generic-rank-4 prescribed-torsion family induced by Diophantine triples. |
| **ℤ/2ℤ × ℤ/6ℤ** | | |
| [Jaswal C2 × C6 Genus-One Rank 4](families/jaswal_c2xc6_rank4/) | 0.1.0 | Jaswal's infinite C2 × C6 family of rank at least 4. |
| [Z/2 x Z/6 Rank-2 Families](families/c2xc6_rank2_families/) | 0.1.0 | Five pairwise non-isomorphic Z/2 x Z/6 families of exact generic rank 2. |
| [Dujella–Peral Joint C2 × C6 Rank-2 Families](families/dujella_peral_joint_2026_c2xc6/) | 0.1.0 | Four new inequivalent rank-2 variants U3, U4, U7, and U9 (2026). |
| **ℤ/2ℤ × ℤ/8ℤ** | | |
| [C2 × C8 · Naskręcki Channel Search](families/c2xc8_channel_search/) | 0.1.0 | Experimental bounded exact point search on C2 × C8 fibers, with Family and Target adapters; no generic rank claim. Requires Rank Hunter 0.10.1 or newer. |
| **Misc.** | | |
| [Mazur Torsion Families](families/mazur_torsion_families/) | 0.2.3 | Candidate lanes across all 15 rational torsion groups. |

Each Family README/provenance file states its exact scientific claim boundary. A literature theorem, a verified generic lower bound, a specialized exact rank, and a heuristic search score are not interchangeable.

## Published Features and Workspaces

| Plugin | Version | Description |
| --- | ---: | --- |
| **Features** | | |
| [Symmetry Reducer](extensions/symmetry_reducer/) | 2.1.1 | Exact search-space symmetry reduction for supported Campbell, Kihara, and Mestre/Fermigier searches. |
| **Workspaces** | | |
| [Curve Explorer](extensions/curve_explorer/) | 0.5.0 | Interactive real-locus Graph plus complex affine 3D projection with exact P/Q -> R -> -R playback for stored curves. |
| [Leaderboard Compare](extensions/leaderboard_compare/) | 0.2.1 | Compare Rank Hunter curves with synchronized high-rank leaderboard data and torsion filters. |
| [Fiber Atlas](extensions/fiber_atlas/) | 0.4.1 | Deprecated in newer Rank Hunter versions. Read-only family atlas with authoritative family-baseline rank-jump/excess semantics, research views, large-family fastpaths, and explicit hashed handoffs to Target Search and Pipelines. |
| [Twist & Isogeny Lab](extensions/twist_isogeny_lab/) | 0.5.2 | Deprecated in newer Rank Hunter versions. Exact rational isogeny classes, bounded quadratic twists, large-curve exact probes, and deterministic research handoffs with explicit proof boundaries. |

## Validation and provenance

Published plugins are expected to preserve source/provenance, distinguish heuristic signals from exact or rigorous evidence, keep plugin-local scientific runners write-free where core owns persistence, and pass focused tests plus current-core manifest/adapter validation before publication.

If a plugin produces unexpected mathematics, report the plugin name/version, Rank Hunter version, curve or parameter, and the failing command/log.

## Plugin author guides

- [Writing a Family plugin](docs/FAMILY_PLUGINS.md)
- [Writing a Feature plugin](docs/FEATURE_PLUGINS.md)
- [Writing a Workspace plugin](docs/WORKSPACE_PLUGINS.md)
- [Documentation index](docs/README.md)

For Rank Hunter itself, see the [Rank Hunter repository](https://github.com/crhillresearch/rank-hunter).
