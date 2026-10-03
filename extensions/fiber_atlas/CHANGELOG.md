# Changelog

## 0.4.1

### Fixed

- Live Mestre/Fermigier validation confirmed the authoritative family baseline at ≥11, a maximum stored rigorous lower of 19, 196 fibers above the recorded baseline, and maximum baseline excess +8.
- Corrected the inspected-fiber dropdown so lower-bound-only families say `excess` instead of `jump`; exact-generic-rank families still say `jump`.

---

## 0.4.0

### Corrected scientific semantics

- Rank-jump calculations now use one authoritative family-level generic baseline instead of subtracting each specialization row's own `generic_lower`.
- Completed `family_evidence` is preferred when available; otherwise Fiber Atlas reads the installed family manifest's recorded generic-rank lower bound.
- A specialization's `generic_lower` remains part of its rigorous specialization lower evidence, but is never reused as the family baseline.
- Exact generic-rank baselines produce true rank-jump labels.
- Lower-bound-only family baselines produce explicitly labeled **baseline excess** values so Fiber Atlas does not overclaim an exact generic-rank jump.
- Baseline value/source/status are surfaced in summary cards, hover text, tables, and selection provenance.
- Preserves the v0.3.x large-database lazy Search-yield / Bad-prime fastpaths.

---

## 0.3.3

### Fixed

- Removed bad-prime parsing from ordinary family switching so large families do not touch expensive prime metadata during normal Landscape/Farey/Rank-jump browsing.
- Replaced unbounded sqrt(n) trial division with a fast Miller-Rabin screen for stored prime labels, preventing huge bad-prime values from pinning Streamlit.
- Made the Bad-prime fingerprint explicitly lazy behind a load button.
- Preserved the v0.3.2 lazy Search-yield path and bounded chart/table rendering.

---

## 0.3.0

### Added

- Added bounded explicit selection of the current filtered region or chosen stored fibers.
- Added deterministic normalized selection payloads with SHA-256 selection hashes.
- Added exact selection provenance: family, curve IDs, parameter strings, view, axes, filters, and parameter/rank/score envelope.
- Added **Target Search** handoff through a new core-owned UI handoff contract.
- Added **Pipelines** context handoff without mutating Builder modules, candidate sources, or scientific state.
- Added inspectable handoff JSON before routing.

### Core contract

- Requires the current Rank Hunter v0.9.x core research-selection handoff helpers. Plugins do not write private Builder session-state keys directly.

---

## 0.2.0

### Added

- Added **Landscape**, **Farey / denominator**, **Rank jumps**, and **Search yield** research modes.
- Added root-number, exact-rank-status, rigorous-lower, rational-height, and denominator-height filters.
- Added read-only durable search-yield projections from point discoveries, quartic searches, covering-search attempts, and rigorous point witnesses.
- Added exact stored bad-prime fingerprint summaries with conservative JSON parsing that does not confuse valuations/exponents with primes.
- Added bounded deterministic SVG projection for large stored families while preserving high-signal fibers.
- Expanded hover and table metadata with durable search-yield and bad-prime information.

### Scientific boundary

- All new modes remain descriptive/read-only. Search-yield and prime patterns are research/scheduling signals, not rank evidence.

---

## 0.1.0

### Added

- Initial **Fiber Atlas** Workspace.
- Read-only family inventory and stored-fiber projection backend.
- Exact rational parameter parsing with numerator, denominator, rational height, and denominator-height coordinates.
- Current stored rigorous-lower and rank-jump projections without recomputing or promoting evidence.
- Theme-aware SVG landscape with configurable axes and color encodings.
- Hover details for individual stored fibers.
- Family summary metrics and full stored-fiber table.
- Ordinary Curves-page handoff for reopening a selected stored fiber.
- Explicit heuristic/proof boundary throughout the Workspace.
