# Elkies Rank-17 K3 · v1.3.1

Rank Hunter Family plugin for Noam D. Elkies's elliptic K3 surface of exact Mordell-Weil rank 17 over `Q(t)`.

Release-audited for Rank Hunter **0.9.2**.

## Mathematical source

Noam D. Elkies, *An elliptic K3 surface X/Q(t) with Mordell-Weil rank 17, I: Formulas for X and base changes of ranks 18 and 19*, arXiv:2608.25406v1, submitted 26 August 2026.

- arXiv: https://arxiv.org/abs/2608.25406
- DOI: 10.48550/arXiv.2608.25406
- Main family statement: Theorem 4 and §2.2.

The surface is

```text
y^2 = x^3 - 27*S(t)*x + (27/4)*T(t)
```

with `deg S = 8` and `deg T = 12`.

The paper exhibits 17 integral sections and computes their height-pairing Gram matrix. Its determinant is `948`, so those sections are independent. Elkies also states that rank 17 is the largest possible Mordell-Weil rank over `Q(t)` for an elliptic K3 surface, giving exact generic rank 17.

## Exact reconstruction bundled here

`family.json` contains the exact published surface and all 17 section coordinates.

The paper prints all 17 `x_i(t)`, prints `y_1(t)`, and gives the leading-coefficient signs

```text
-+-+++++-+-+++-++
```

for `y_1,...,y_17`.

The remaining `y_i` were reconstructed exactly as degree-6 polynomial square roots of the published right-hand side. The release self-check:

- verifies all 17 section identities exactly;
- recomputes Elkies's height pairing from the bundled formulas;
- matches the stored published Gram matrix entry-for-entry;
- checks determinant `948`.

The published height data are stored in `data/published_height_gram.json`.

## Claim boundary

The generic family has exact rank 17 by Elkies's theorem.

That statement is **not** automatically copied to a rational specialization. For each specialized fiber Rank Hunter:

1. specializes the 17 bundled sections exactly;
2. verifies they lie on the specialized curve;
3. promotes a rigorous specialization lower bound only after the exact independence certificate succeeds.

Likewise, `ratpoints` and classical 2-covering hits are exact rational points, but they count as rank growth only after exact independence certification.

A timeout or failed covering search is inconclusive.

## Capabilities

```text
candidate_generation
family_search
target_search
known_subgroup
free_search
```

### Candidate generation

The plugin uses Rank Hunter's staged Nagao/Mestre candidate engine. The score is a search heuristic, not rank evidence.

Default candidate box:

```text
a = -5000 .. 5000
b = 1 .. 1000
prime stages = 1000,2000,4000
stage keeps = 20000,4000,500
final candidates = 500
```

### Family Search

For each candidate the runner can:

- instantiate the exact specialization;
- specialize and optionally certify the 17-section baseline;
- run staged direct `ratpoints`;
- store exact mapped points;
- test candidate extras with Rank Hunter's exact lower-bound certificate.

Expensive 2-covering work remains opt-in for ordinary Family Search.

### Target Search

Target Search exposes the deeper record-hunt path:

- direct `ratpoints`;
- optional rigorous mwrank 2-Selmer upper-bound gate;
- Denis Simon known-point two-descent or full eclib/mwrank two-descent;
- hard wall-clock timeouts around covering workers;
- exact certification of every promoted extra direction.

The default research target is rank at least 31. The Selmer gate may prune only the expensive target-specific covering stage when its rigorous upper bound is already below that target. It never deletes lower-bound evidence or converts a timeout into a negative result.

## Auto Search policy

The plugin exposes the 17-section subgroup to core Auto Search.

Rank Hunter's current policy is:

1. exact-certify the specialized 17-section baseline;
2. while the rigorous lower bound is below 25, search denominator-1 x on a global minimal integral model;
3. once the rigorous lower reaches 25, unlock general exact affine/rational x charts;
4. exact-certify every accepted new direction.

The rank-25 switch is a **Rank Hunter search policy**, not a claim about Elkies's historical search schedule.

## Published high-rank control fibers

The paper gives these useful specialization controls:

```text
t = -2/377       rank >= 25
t = -308/251     rank >= 26
t = 2456/135     rank >= 27
t = -9529/5471   rank >= 28
```

These are literature controls. The plugin does not pre-label a local curve with those lower bounds unless Rank Hunter has corresponding rigorous local evidence.

## Validation

From the plugin repository, set `RANK_HUNTER_ROOT` to your Rank Hunter core checkout:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python -m pytest -q families/elkies_rank17_2026/tests
```

The release gate includes current-core plugin validation and the exact height-Gram self-check.

The standalone self-check remains:

```bash
PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python families/elkies_rank17_2026/verify_family.py
```

Expected key output includes:

```text
sections_verified_on_curve: 17
published height Gram: MATCH
determinant: 948
sections: 17
```

## Release separation

The recovered **Elkies Rank-18 First Cover** is maintained as its own Family package and is audited separately. Rank-18 reconstruction data/scripts are therefore not bundled into this Rank-17 RELEASE package.

## Version history

### v1.3.1

Rank Hunter 0.9.2 release audit. Corrects arXiv provenance, removes stale 0.8.x/install-package wording, isolates the separate Rank-18 First Cover material, and adds current-core release validation while preserving the v1.3 search behavior.

### v1.3.0

Exposed the exact 17-section subgroup to the primary record-hunt path, including staged direct search, rigorous target gating, classical 2-covering search, and current Auto Search policy.
