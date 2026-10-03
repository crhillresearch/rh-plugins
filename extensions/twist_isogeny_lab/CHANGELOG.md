# Changelog

## 0.5.2

### UI polish
- Kept the full-class timeout selector inline with the compute action.
- Added bottom spacing below the Research-mode proof-boundary cards.
- No scientific or persistence semantics changed.

## 0.5.1

### Visible research hierarchy
- Added explicit numbered Source / Mode / Selected object / Neighborhood stages.
- Added theme-aware source, proof-boundary, and selected-object cards.
- Added exact/stored/interpretation boundary panels for the active research mode.
- Clarified that computed twist, isogeny-class, and probe payloads are session-cached only.
- No scientific arithmetic, proof authority, database persistence, or handoff semantics changed.

## 0.5.0

### Researcher polish
- Added a top-of-page source arithmetic brief with stored evidence/model context.
- Added mode-specific exact/stored/heuristic boundary text before expensive actions.
- Moved twist and isogeny selected-object inspectors above dense result views.
- Kept full exact arithmetic available in progressively disclosed expanders.

## 0.4.0

### Research handoffs
- Added deterministic, inspectable multi-selection handoffs for exact isogeny-class nodes and bounded quadratic twists.
- Added handoffs for successful exact one-hop large-curve probe hits while preserving their partial-class provenance.
- Retained curve matches now carry Twist Lab provenance into ordinary Curves / Target Search ownership.
- Pipeline handoffs use the core research-selection contract and never write private Builder state or launch work.

## 0.3.1

### Fixed
- Prime-degree source probes now pass the requested degree to Sage as a Sage Integer (`ZZ`) rather than a Python `int`, preventing large-curve probe failures in code paths that call `.is_prime()` on the degree.

## 0.3.0

### Large-curve resilience
- Complete Sage isogeny-class timeouts are explicitly inconclusive.
- Added selectable 30/90/300/900 second complete-class bounds.
- Added exact one-hop prime-degree source probes with isolated per-degree timeouts.
- Completed degrees retain exact hit/no-hit status even when another degree times out.
- Successful probe hits preserve exact codomain models and arithmetic metadata.

### Research ergonomics
- Compact huge twist conductors by digit count/preview in the main table.
- Show bad-prime count, compact support, and support changes from the source.
- Preserve full exact conductor, discriminant, bad-prime support, and minimal model in the inspector.

## 0.2.0

- Added bounded squarefree quadratic-twist neighborhoods for both signs.
- Added exact Sage conductor/discriminant/bad-prime/root-number/torsion metadata.
- Added retained-evidence projection, filters, sorting, and read-only retained-curve handoffs.

## 0.1.0

- Initial exact rational-isogeny-class workspace.
- Added prime-degree isogeny graph, exact node arithmetic, retained source projection, and core-owned curve handoffs.
