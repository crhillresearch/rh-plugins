# Changelog

## 1.2.0

- Audit the Family for Rank Hunter 0.9.2 public RELEASE.
- Add an exact generic lower-bound-14 certificate at Kihara's published `t=2` proof control.
- Preserve the theorem as rank-at-least-14; do not claim exact generic rank 14.
- Refresh Kihara paper/proof provenance and specialization claim boundaries.
- Replace developer-local install/verification guidance with portable release commands.
- Add current-core release regression coverage.

## 1.1.1

- Adopt the v0.8.7.1 historical-vs-verified generic-rank manifest contract.
- Stop advertising Kihara's published rank-14 theorem as an operational generic lower bound.
- Require the core exact lower-bound certificate before writing specialization `generic_lower=14`.
- Store certified specialized sections as rigorous witnesses in the unified point ledger.
- Clear unsupported legacy `generic_lower` values left by v1.1.0 numerical screens.
- Keep canonical-height checks as numerical novelty screens only.
- Replace covering `generic_rank` metadata with historical claim metadata.
- Add an operator-configurable exact-certificate timeout.

## 1.1.0

- Make the family fully standalone for Rank Hunter v0.8.7.1+.
- Move all Kihara-specific family and search mathematics into the plugin package.
- Stop dispatching to removed `rank42.kihara_*` / `rank42.families.*` modules.
- Use plugin-local worker paths from the thin search adapter.
- Make `search_options(context=...)` compatible with the v0.8.7.1 family/target UI contract.
- Add release documentation, provenance ledger, doctor check, and regression tests.

## 1.0.0

- Initial manifest/adapter wrapper used while Kihara scientific code still lived in Rank Hunter core.
