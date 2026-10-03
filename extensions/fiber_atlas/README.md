# Fiber Atlas v0.4.1

**Fiber Atlas** is a read-only Rank Hunter Workspace for seeing an elliptic-curve family as a parameter-space landscape instead of a list of unrelated specializations.

## Research views

### Landscape

Configurable X/Y/color exploration over durable stored fields including rational-parameter geometry, Nagao score, rigorous lower bound, rank jump, and root number.

### Farey / denominator

A rational numerator/denominator coordinate view using signed log numerator versus log denominator. This is **not** a Farey adjacency graph; it is a descriptive view of where tested rational parameters concentrate.

### Rank jumps

Shows specialization rigorous lower bounds relative to one authoritative family-level generic baseline. Fiber Atlas first uses completed family-level evidence when available and otherwise falls back to the installed family manifest's recorded generic lower bound. It never reuses a specialization row's mutable `generic_lower` as the family baseline.

### Search yield

Projects durable previous-search artifacts onto family parameter space:

- exact point-discovery events;
- persisted quartic hits;
- mapped points from covering-search attempts;
- stored rigorous-independent point witnesses.

These counts describe where previous search work produced objects. They are not rank predictors or proofs by themselves.

## Filters

Fiber Atlas can filter the current family by:

- stored root number;
- exact-rank status versus lower-bound-only status;
- rigorous lower-bound band;
- logarithmic rational-height band;
- logarithmic denominator band.

Leaving a range at its full extent is nonrestrictive, so rows with unknown metadata are not silently excluded from unrelated modes.

## Bad-prime fingerprint

When `curves.bad_primes_json` contains exact stored bad-prime data, Fiber Atlas summarizes prime incidence across the current filtered fibers.

Only explicit prime slots are parsed. Valuations, exponents, counters, and arbitrary metadata integers are not reinterpreted as primes.

The fingerprint is descriptive exact metadata; any visible association with high rank remains heuristic research interpretation.

## Performance

The family table remains complete, while the SVG plot is bounded to a deterministic maximum display population. High-signal fibers are preserved first and the remaining cloud is sampled deterministically so large families do not create unbounded browser payloads.

## Curve handoff

A selected stored fiber can be reopened through Rank Hunter's ordinary **Curves** page. Fiber Atlas does not create a parallel curve-detail system.

## Scientific boundary

Fiber Atlas performs **no rank computation and no scientific database writes**.

The Workspace visualizes evidence and research artifacts Rank Hunter already stores. In particular:

- Nagao score is heuristic scheduling evidence;
- visible clusters and parameter-space neighborhoods are exploratory patterns;
- root-number patterns may guide research but do not certify rank;
- search-yield patterns describe prior productivity, not mathematical rank;
- a displayed rigorous lower bound is only the maximum of the rigorous lower-bound fields already stored on the curve row;
- the family baseline is resolved independently from family-level evidence or the installed family manifest;
- when the exact generic rank is known, `rigorous lower - exact generic rank` is displayed as a true rank jump;
- when only a generic lower bound is recorded, the difference is labeled baseline excess and is **not** by itself proof of a jump above the unknown exact generic rank;
- exact rank is shown only when Rank Hunter already stores `exact_rank`.

The atlas never promotes a heuristic signal into proof.

## Validation

From the Rank Hunter runtime checkout after installing the package at `plugins/fiber_atlas`:

```bash
PYTHONPATH="$PWD" python -m pytest -q plugins/fiber_atlas/tests
```


## Selection handoffs

Fiber Atlas can now turn the current filtered region, or an explicitly chosen subset of stored fibers, into a normalized research-selection payload.

The payload records:

- family;
- explicit stored curve IDs and exact parameter strings;
- current Atlas view;
- X/Y/color projection;
- active filters;
- rational-parameter/score/rank envelope;
- a deterministic SHA-256 selection hash.

The Workspace caps one handoff at 250 fibers so the selection stays explicit and inspectable.

From the selection panel:

- **Open curve** routes the chosen primary fiber to the ordinary Curves page;
- **Target Search** routes the primary fiber to Rank Hunter's ordinary Target page while carrying the full selection as provenance;
- **Pipelines** routes the full selection to the ordinary Pipeline editor as context only.

Fiber Atlas never launches a search itself. In particular, the Pipeline handoff does not alter Builder modules, candidate sources, rank goals, or create a run. Current core does not yet expose a generic arbitrary-parameter-list population contract, so the Pipeline page shows the exact selection and lets the researcher choose an ordinary supported source/recipe.


## Family baseline semantics

Fiber Atlas now separates two ideas that older databases may blur:

- **specialization rigorous lower**: the best stored rigorous lower on one curve row, from `exact_rank`, `descent_lower`, and `generic_lower`;
- **family baseline**: one family-level generic-rank reference resolved independently of specialization promotion state.

Resolution order:

1. completed `family_evidence` for the stored family specification/fingerprint;
2. the installed family plugin manifest's verified/declarative `generic_rank` lower bound.

Fiber Atlas does not infer a family baseline from high specialization rows.

For the Mestre/Fermigier sextuple family, the installed plugin records generic rank at least 11. A specialization with rigorous lower 19 therefore displays **+8 above the recorded generic lower bound**. Because the family claim is a lower bound rather than an exact generic rank theorem, that +8 is baseline excess, not automatically proof that the specialization rank jumps by exactly eight above the true generic rank.

When family evidence establishes an exact generic rank, Fiber Atlas upgrades the wording to a genuine rank jump.
