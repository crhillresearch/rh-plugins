# Twist & Isogeny Lab v0.5.2

**Twist & Isogeny Lab** is a read-only Rank Hunter Workspace for exploring the arithmetic neighborhood around one retained elliptic curve.

## v0.5.2 — inline control polish

- aligned the full-class timeout selector with the compute button by collapsing its external label and rendering the timeout inside the select value;
- added bottom breathing room below the EXACT / STORED / INTERPRETATION cards so they no longer touch the Research-mode container border;
- presentation only; no arithmetic, evidence, cache, or handoff semantics changed.

## v0.5.1 — visibly staged research workspace

The Workspace now presents an explicit four-stage visual hierarchy: **1 Source curve → 2 Research mode → 3 Selected object → 4 Neighborhood results**.

- added numbered, theme-aware stage banners so the page reads as a deliberate research workflow rather than a loose collection of controls;
- upgraded the retained source into a stronger bordered source card;
- made the research mode its own bordered area with separate **EXACT / STORED / INTERPRETATION** boundary panels;
- made selected twist / selected isogeny-node inspectors real bordered object cards before dense neighborhood data;
- labels computation caches as session-only so a restart, browser-session reset, or plugin reload is clearly understood to require recomputation;
- no arithmetic, rank-evidence, handoff, or database-persistence semantics changed.

## v0.5.0 — researcher-facing layout polish

The Workspace reads from source context → research mode → selected object → dense neighborhood data, instead of making the user scroll through large result tables before seeing exact object details.

- added a top-of-page **Source arithmetic brief** with family/parameter, stored lower bound, compact conductor/discriminant, root/Nagao, and exact stored a-invariants;
- added mode-specific text at the top that states what the current view computes exactly, what comes from stored Rank Hunter evidence, and what remains heuristic or inconclusive;
- moved the quadratic-twist inspector above the dense twist table;
- moved the isogeny-node inspector above the graph/class tables;
- exact conductor/discriminant/j/torsion/model details remain available through compact expanders instead of dominating the default layout.

## v0.4.0 — deterministic selection handoffs

Twist & Isogeny Lab can now turn exact arithmetic-neighborhood selections into inspectable core-owned research context without becoming a parallel search engine.

- select one or more exact isogeny-class nodes and send the normalized selection to **Pipelines**;
- select one or more bounded quadratic-twist squareclasses and send their exact models/arithmetic to **Pipelines**;
- successful large-curve prime-degree probe hits can also be handed off as explicitly partial one-hop isogeny selections;
- retained exact-model/source matches preserve Workspace provenance when reopening **Curves** or entering **Target Search**;
- every handoff carries the retained source curve, exact selected objects, retained-match IDs, a deterministic SHA-256 selection hash, and relevant class/twist/probe provenance;
- Pipeline handoff is context only: the Workspace does not alter Builder modules, candidate sources, rank goals, or create a run.

## v0.3.0 — large-curve resilience + researcher ergonomics

Record-size curves can make a complete Sage isogeny-class computation exceed an interactive timeout. v0.3.0 treats that correctly as **inconclusive**, not as evidence that the class is trivial.

The Isogeny view now adds:

- selectable full-class timeouts: 30s / 90s / 300s / 900s;
- an exact one-hop source probe over rational prime isogeny degrees;
- per-degree isolation, so a timeout at one degree does not erase exact results from completed degrees;
- explicit `exact hit`, `exact no hit`, and `timeout / unknown` status labels;
- exact codomain models for successful prime-degree source isogenies.

The quadratic-twist table now keeps huge arithmetic readable by showing conductor size, bad-prime count, compact bad-prime support, and support changes relative to the source. Full exact conductor, discriminant, bad-prime list, and minimal a-invariants remain available in the twist inspector.

## v0.2.0 — isogeny + bounded quadratic twists

The Workspace now has two research views:

- **Isogeny class** — exact rational isogeny graph over `Q`, with retained Rank Hunter evidence projected only onto safely matched nodes.
- **Quadratic twists** — exact squarefree twist classes for both signs up to a user-selected `|d|` bound (hard cap 250), computed only on demand and cached by source curve/bound.

For each twist the Sage worker reports exact model/minimal-model coefficients, conductor, discriminant, bad primes, root number, `j`-invariant, and rational torsion invariants. Stored rigorous lower / exact-rank / Nagao fields appear only when Rank Hunter already retains an exact matching model, or for the explicitly identified `d=1` source squareclass.

The twist table can filter by root sign and retained status, and sort by `|d|`, stored rigorous lower, stored Nagao, or conductor. Viewing an unstored twist never inserts it into the Rank Hunter database.

## v0.1.0 — isogeny MVP

The first release focuses on the rational isogeny class over \(\mathbf Q\):

- starts from a retained Rank Hunter curve;
- computes the exact rational isogeny class through the configured scientific Python/Sage runtime;
- displays exact Weierstrass coefficients, direct prime-degree isogeny edges, conductor, discriminant, \(j\)-invariant, root number, and rational torsion invariants;
- joins nodes back to retained Rank Hunter curves by canonicalized exact rational model coefficients;
- preserves the selected retained source as an explicitly labeled exact `Q`-isomorphic match when Sage chooses a different model for that source node;
- projects already-stored rigorous lower / exact-rank / Nagao metadata onto retained matches without creating new evidence;
- routes stored matches through ordinary Curves / Target Search ownership.

The expensive Sage computation runs only when explicitly requested and is bounded by a hard timeout. Ordinary page reruns do not recompute the class.

## Scientific boundary

The isogeny graph/model arithmetic shown here is exact arithmetic from Sage. Stored Rank Hunter rank fields remain whatever evidence class core already assigned to those rows.

Twist & Isogeny Lab:

- does **not** compute or promote rank evidence;
- does **not** insert isogenous curves into the Rank Hunter database merely because they are visible;
- does **not** launch searches itself;
- does **not** treat root number, Nagao score, or neighborhood structure as proof of rank.

Quadratic-twist root-number / conductor / bad-prime structure is exact arithmetic; using those patterns to prioritize future searches remains heuristic. Selection handoffs to Pipelines and retained-curve Target Search are deterministic research context only; they do not launch work or promote rank evidence.
