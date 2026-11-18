# C2 × C8 Naskręcki Channel Search

This experimental Family plugin supplies exact rational-point candidates for a
published C2 × C8 family. It does not claim a generic free rank. It complements
Rank Hunter's existing Mazur C2 × C8 universal provider, which is unchanged.

For a reduced rational parameter `t=a/b`, with `b>0`, set `D=a²-b²` and
`M=2ab`. The plugin searches the integral model

```text
Y² = X(X + D⁴)(X + M⁴).
```

It is isomorphic over Q to `y²=x(x+1)(x+u⁴)`, `u=M/D`, by
`X=D⁴x`, `Y=D⁶y`. A stored curve with a different model receives points only
after Sage verifies a Q-isomorphism and applies its exact point map.

## Search and coverage

Write a primitive rational point as `x=X/Z²`, `y=Y/Z³`, with `Z>0` and
`gcd(X,Z)=1`. For `X≠0`, each prime dividing `X` to an odd power divides
`D*M`. Thus `X=d*k²`, where `d` is a signed squarefree divisor supported on
the completely factored `D*M`. The worker enumerates bounded `d,k,Z`, applies
quadratic-residue filters, then checks the full integer equation with `isqrt`
and Sage. It emits both signs before optional torsion-orbit deduplication.

`|X| bound` and `Z bound` define the box. `k cap`, pair/point budgets, a factor
timeout, a wall timeout, or cancellation can cut it short. Only a full
factorization and untruncated squareclass scan earn `bounded_complete`.
`grid_control` is an independent bounded `X,Z` comparison, and is never
described as a completed squareclass scan. If factoring fails, the fallback
grid is marked partial for the squareclass task. A partial scan proves no
absence of points or rank upper bound.

Exact points are candidate evidence. Modding out sign and the rational torsion
orbit reduces duplicate supply; it does not test dependence on free points.
Rank Hunter core checks every returned point and owns independence/rank
certification. Candidate and certification-attempt fingerprints are separate,
so a reused point can be retested against a changed certified seed set.

The worker writes typed results to `RANK42_PLUGIN_GEOMETRY_RESULT_PATH` and
checkpoints under `.rank42-ui/channel-checkpoints/`. It reads a temporary DB
copy supplied by core and never writes to the live DB. Family Search uses
core's one-candidate-per-worker contract. Target Search requires a curve
created by this plugin and a verified parameter/model map; foreign C2 × C8
curves are reported as `needs_verified_parameter_map`.

## Pipeline record hunt

In Pipelines, choose **Family** and this channel family, then load **C2×C8
Record Hunt**. It sets a rigorous rank goal of 4 and, when the job ends, keeps
new curves with rank at least 3. The preset scans primitive parameters in
`-400 ≤ a ≤ 400`, `1 ≤ b ≤ 120`, screens at two prime bounds, and takes 200
candidates forward.
It checks exact torsion and tries a short rigorous upper-bound gate before
searching points. A proved upper bound below 4 removes a fiber from this
record hunt; a timeout or inconclusive bound does not.

The channel scan runs on a smaller shortlist, then a deeper channel scan,
coverings, denominator searches, and high-height work run only on survivors.
The final Record Breaker Lane opens only for fibers that have already reached
rigorous rank 3.
The preset uses the plugin's Family and Target adapters. It does not require
the Euler or lattice-chart hooks that this family does not implement. A rank
record needs four independently certified points and exact C2 × C8 torsion;
quartic hits and point counts alone do not meet that goal.

## Reproduce the control

From the Rank Hunter checkout:

```bash
RANK42_PLUGIN_GEOMETRY_RESULT_PATH=/tmp/c2xc8-channel-result.json \
  sage -python plugins/families/c2xc8_channel_search/search_runner.py \
  --mode direct --parameter 4 --x-abs-max 800 --z-max 1 \
  --max-points 1000 --torsion-orbit-dedupe false
sage -python -m rank42.plugin_validate --project-root . \
  --db /tmp/c2xc8-validation.db --plugin c2xc8_channel_search
sage -python -m pytest -q \
  plugins/families/c2xc8_channel_search/tests
```

The control returns `(800, ±448800)` from `d=2,k=20,Z=1` on
`[0,54721,0,207360000,0]`. The test suite checks the exact torsion structure,
the order-8 point, and `[16](800,448800)≠O`.

The same model occurs at `t`, `-t`, `1/t`, and `-1/t` where defined. The worker
records the primitive parameter and canonical same-model orbit. Core candidate
generation removes sign duplicates; completed exact scans are cached across
the inverse orbit under `.rank42-ui/channel-cache/`. Each target still gets
its own seed-set and certification-attempt fingerprint. No further
parameter equivalence is assumed from a matching `j`-invariant.

The quadratic-cover and base-change ideas in the brief are future research
work. This version implements the bounded exact generator and its core handoff.
