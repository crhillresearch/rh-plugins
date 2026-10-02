# Nagao · j=1728 Rank ≥4 Twist Family

This plugin reconstructs Koh-ichi Nagao's 1994 family

```text
E_t : y^2 = x^3 - k(t)x
```

with modular invariant `j=1728` and four independent rational sections.

Nagao starts from four rational functions `a(t),b(t),c(t),d(t)` satisfying

```text
a(t)^4 + b(t)^4 = c(t)^4 + d(t)^4
```

and takes `k(t)=a(t)^4+b(t)^4`. The four sections are

```text
(-a^2, a b^2), (-b^2, b a^2), (-c^2, c d^2), (-d^2, d c^2).
```

At the paper control `t=3`:

```text
(a,b,c,d) = (133,-134,158,-59)
k = 41·113·241·569 = 635318657.
```

Nagao proves those four sections are independent and uses Silverman's
specialization theorem plus a non-isomorphism argument to obtain infinitely many
pairwise non-Q-isomorphic curves with rank at least 4.

## Claim boundary

This is a **generic lower-bound-4** Family. Nagao does not prove exact generic
rank 4, and Rank Hunter does not claim it.

## Exact symmetry

The factored `k(t)` is even, so `t` and `-t` give the same curve. The
plugin declares exact sign symmetry, allowing Candidate Generation to keep one
representative from each orbit.

## Search

Candidate Generation, Family Search and Target Search are all supported.
Family/Target Search reconstructs Nagao's four exact sections and then runs
bounded completed-square ratpoints for extras. The runner is write-free; Rank
Hunter core validates every point and owns all independence/rank promotion.

A current 2026 survey cites a Watkins `j=1728` curve over Q of rank 14, so
record-oriented search profiles target rank 15.

## Source

Koh-ichi Nagao,
*On the rank of elliptic curve y² = x³ − kx*,
Kobe Journal of Mathematics 11 (1994), 205–210.
