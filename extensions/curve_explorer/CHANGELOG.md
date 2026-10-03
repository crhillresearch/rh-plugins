# Changelog

All notable changes to **Curve Explorer** are documented here.

Curve Explorer is a Rank Hunter extension for interactively exploring elliptic curves, rational points, and the elliptic-curve group law.

---

## 0.5.0

### Added

- Added page-level **Graph** and **3D** views while preserving the existing Graph workspace.
- Added an interactive complex affine projection rendered without an external plotting dependency.
- The 3D view can switch between `(Re x, Im x, Re y)` and `(Re x, Im x, Im y)`, orbit by dragging, zoom with the wheel, reset the camera, and auto-rotate.
- Added real-locus highlighting and stored rational-point overlays in the complex projection.
- Added a bounded backend sampler for the two complex y-branches of a generalized Weierstrass model.
- Added explicit visualization/proof-boundary text: the 3D projection omits the point at infinity and apparent crossings may be projection artifacts.

### Inspiration

- The complex-to-`R^3` presentation is inspired by Arapura's Purdue elliptic-curve visualization page; Curve Explorer samples Rank Hunter's generalized affine Weierstrass equation directly rather than requiring a period-lattice / Weierstrass-℘ computation.

---

## 0.4.8

### Fixed

- **Construct** no longer stays disabled merely because a selected P/Q pair falls outside the bounded precomputed pair cache.
- Added exact BigInt rational secant/tangent arithmetic in the embedded explorer for uncached selected pairs, matching the generalized Weierstrass formulas used by the Python backend.
- Cached pairs still use backend-precomputed exact data; uncached pair arithmetic is computed only on selection and remains visualization-only.
- The bounded initial pair cache is preserved to avoid quadratic iframe payload growth.

---

## 0.4.7

### Fixed

- Stored-point clicks now reliably assign **P** and **Q** across the full marker hit area.
- Points outside the bounded exact construction cache are no longer inspection-only: they can still be selected as P/Q.
- Exact Construct playback remains enabled only when the selected pair has a precomputed exact cache entry; uncached pairs are labeled clearly and can be handled with Server exact tools.
- Preserved the bounded exact pair-cache policy and all arithmetic semantics.

---

## 0.4.6

### Changed

- Changed the Curve Explorer Extension/page icon from `:material/scatter_plot:` to `:material/insights:`.
- Icon ownership remains plugin-local through the supported manifest contract.

---

## 0.4.5

### Changed

- Replaced the fixed dark-only explorer palette with Rank Hunter's resolved semantic `rh-*` theme tokens.
- The embedded iframe now follows the active Light/Dark appearance for cards, controls, text, borders, curve/point colors, overlays, and tooltips.
- Added appearance-aware fallback tokens for degraded/older hosts without the runtime iframe palette bridge.
- Exact curve arithmetic, stored-point semantics, and group-law construction behavior are unchanged.

---

## 0.4.4

### Fixed

- Exact coordinate display for large multiples no longer fails at Python 3.11+'s default 4,300-digit integer-to-string conversion limit.
- Large integers are rendered exactly in plugin-local base-10 chunks; Curve Explorer does not modify the process-global `sys.set_int_max_str_digits` setting.

---

## 0.4.3

### Changed

- Added the new core-supported Extension navigation icon metadata using `menu.icon = ":material/scatter_plot:"`.
- Keeps icon ownership plugin-local through the public manifest contract; no sidebar or `NAV_ICONS` patching is used.

---

## 0.4.2

### Fixed

- Removed the plugin-local `st.title` so Rank Hunter v0.8.7.1's Extension host is the single owner of the page header.
- Replaced deprecated `streamlit.components.v1.html` embedding with `st.iframe` while preserving the interactive SVG/JavaScript explorer.

---

## 0.4.1

### Changed

- Added a dark plotting surface designed to fit naturally with Rank Hunter's Nightstream-style interface.
- Updated grid lines, axes, labels, controls, hover cards, and construction markers for improved contrast on dark backgrounds.

---

## 0.4.0

### Added

- Direct point selection from the curve visualization.
  - First selected point becomes \(P\).
  - Second selected point becomes \(Q\).
  - Selecting the same point twice performs the tangent/doubling construction.
- Interactive visualization of the full elliptic-curve group-law construction:
  - \(P\) and \(Q\)
  - secant or tangent line
  - third intersection \(R\)
  - reflected point \(-R=P+Q\)
- Animated **Construct** sequence showing the geometric addition process.
- Point-display filters:
  - All points
  - Generators
  - Selected subgroup
- Hover-based labels for ordinary stored points to keep high-rank curves readable.
- Smart automatic framing designed to avoid extreme-coordinate outliers dominating the initial view.
- Additional framing controls:
  - Smart
  - Fit shown
  - Fit all
  - Curve
  - Fit construction
- Exact precomputation of supported \(P,Q\) constructions in Python before visualization.
- Bounded direct-click construction support for large point sets.

### Changed

- Reduced persistent point labels in favor of hover details.
- Improved visualization behavior for curves with many known rational points.

---

## 0.3.0

### Added

- Major visual redesign inspired by interactive elliptic-curve teaching tools.
- Large curve-first visualization replacing the earlier dashboard-style plot.
- Continuous rendering of the real elliptic curve rather than displaying rational points alone.
- Numbered coordinate axes and a cleaner mathematical grid.
- Rational-point overlays directly on the real locus.
- Distinct markers for:
  - \(P\)
  - \(Q\)
  - \(P+Q\)
- Secant/tangent line rendered directly on the graph.
- Point inspection with exact rational coordinates.
- Interactive graph controls:
  - drag to pan
  - mouse-wheel zoom
  - double-click zoom
  - Fit points
  - Reset
  - zoom in/out
- Compact curve metadata/status presentation.
- Multiples and detailed point information moved into secondary expandable sections.

### Changed

- Reworked the extension around a "math instrument" design instead of a monitoring/dashboard layout.
- Gave the elliptic curve itself visual priority over surrounding metadata.

---

## 0.1.x

### Added

- Initial release

---

## Credits

Curve Explorer was inspired in part by the interactive elliptic-curve visualizations in the **MATH5020 Elliptic Curves** project by **@mathandcobb**.

Curve Explorer is an independent Rank Hunter extension and retains Rank Hunter's distinction between visualization, numerical evidence, and rigorous mathematical certification.
