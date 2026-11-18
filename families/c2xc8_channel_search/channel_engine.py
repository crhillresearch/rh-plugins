"""Exact bounded squareclass search on the Naskręcki integral model.

The squareclass restriction is necessary for every primitive rational point.
It does not assert a rank bound, and a partial run does not exhaust a box.
"""
from __future__ import annotations

import itertools
import math
import multiprocessing as mp
import time

from sage.all import QQ, ZZ

from family import curve, parameter_data


ENGINE_VERSION = "0.1.0"
SIEVE_PRIMES = (3, 5, 7, 11, 13, 17, 19, 23)
SQUARE_RESIDUES = {p: {k*k % p for k in range(p)} for p in SIEVE_PRIMES}


def _factor_child(n, output):
    try:
        factors = [(int(p), int(e)) for p, e in ZZ(n).factor()]
        if any(not ZZ(p).is_prime(proof=True) for p, _ in factors):
            raise ArithmeticError("factorization contains an uncertified prime")
        output.put({"complete": True, "factors": factors})
    except BaseException as exc:
        output.put({"complete": False, "error": repr(exc)})


def factor_prime_support(n, timeout):
    """Factor in a killable subprocess; never infer completeness from a timeout."""
    if int(n) < 1:
        raise ValueError("factor input must be positive")
    context = mp.get_context("fork")
    output = context.Queue(maxsize=1)
    process = context.Process(target=_factor_child, args=(int(n), output))
    process.start()
    process.join(max(0.01, float(timeout)))
    if process.is_alive():
        process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join()
        output.close()
        return {"complete": False, "primes": [], "reason": "factor_timeout"}
    try:
        raw = output.get(timeout=1)
    except Exception:
        raw = {"complete": False, "error": "factor worker exited without a result"}
    finally:
        output.close()
    if not raw.get("complete"):
        return {"complete": False, "primes": [], "reason": raw.get("error", "factor_failed")}
    factors = raw["factors"]
    if math.prod(p**e for p, e in factors) != int(n):
        return {"complete": False, "primes": [], "reason": "factor_product_mismatch"}
    return {"complete": True, "primes": sorted(p for p, _ in factors)}


def signed_squareclasses(primes):
    """Deterministic lazy enumeration; +1 and -1 are included."""
    for size in range(len(primes) + 1):
        for subset in itertools.combinations(primes, size):
            d = math.prod(subset)
            yield d
            yield -d


def _square_candidate(X, Z, A, B, modular_sieve):
    zz = Z*Z
    N = X*(X+A*zz)*(X+B*zz)
    if N < 0:
        return None
    if modular_sieve:
        for p in SIEVE_PRIMES:
            if N % p not in SQUARE_RESIDUES[p]:
                return None
    Y = math.isqrt(N)
    return Y if Y*Y == N else None


def _point_records(E, X, Y, Z, *, d=None, k=None):
    z2, z3 = Z*Z, Z*Z*Z
    output = []
    for yy in ((Y,) if Y == 0 else (Y, -Y)):
        xq, yq = QQ(X)/z2, QQ(yy)/z3
        P = E(xq, yq)  # Sage independently checks the exact equation.
        output.append({
            "x": str(P[0]), "y": str(P[1]),
            "X": int(X), "Y": int(yy), "Z": int(Z),
            "d": None if d is None else int(d),
            "k": None if k is None else int(k),
        })
    return output


def search(
    t, *, generator="squareclass", x_abs_max=2000, z_max=2,
    k_max=0, max_points=32, max_candidates=300000,
    factor_timeout=10, run_timeout=90, modular_sieve=True,
    require_full_factorization=True, resume=None, checkpoint=None,
    cancelled=None,
):
    """Return exact points and a precise bounded-coverage status.

    `max_candidates` counts primitive (X,Z) pairs actually considered. A
    checkpoint resumes at the next untested pair, including partial k rows.
    """
    data = parameter_data(t)
    if data is None:
        raise ValueError(f"invalid or singular C2 × C8 parameter: {t}")
    E = curve(t)
    a, b, D, M, A, B = data
    A, B = int(A), int(B)
    x_abs_max, z_max = int(x_abs_max), int(z_max)
    k_max, max_points, max_candidates = int(k_max), int(max_points), int(max_candidates)
    if min(x_abs_max, z_max, max_points, max_candidates) < 1 or k_max < 0:
        raise ValueError("bounds and budgets must be positive; k_max may be zero")
    if generator not in {"squareclass", "grid_control"}:
        raise ValueError(f"unsupported generator {generator!r}")
    requested_generator = generator
    start = time.monotonic()
    deadline = start + max(0.01, float(run_timeout))
    resume = dict(resume or {})
    records = list(resume.get("points") or [])
    seen = {(r["x"], r["y"]) for r in records}
    examined = int(resume.get("examined") or 0)
    examined_this_attempt = 0
    factor = {"complete": False, "primes": [], "reason": "grid_control"}
    if generator == "squareclass":
        prior = resume.get("factor")
        factor = prior if isinstance(prior, dict) and prior.get("complete") else factor_prime_support(
            abs(int(D*M)), min(float(factor_timeout), max(0.01, deadline-time.monotonic()))
        )
        if not factor["complete"]:
            if require_full_factorization:
                return {
                    "status": "inconclusive", "coverage": "bounded_partial",
                    "reason": factor.get("reason", "factor_incomplete"),
                    "factor": factor, "points": records, "examined": examined,
                    "parameter": str(QQ(t)), "a": int(a), "b": int(b),
                    "D": int(D), "M": int(M), "A": A, "B": B,
                    "elapsed_seconds": time.monotonic()-start,
                }
            generator = "grid_control"

    if resume.get("mode") not in (None, generator):
        # A previous factor failure may have run the optional grid fallback.
        # Its cursor has no meaning in a later successful squareclass scan.
        resume.update({"index": 0, "k": None, "z": 1})
    if len(records) >= max_points:
        return {
            "status": "partial", "coverage": "bounded_partial",
            "reason": "point_budget", "factor": factor,
            "points": records, "examined": examined,
            "parameter": str(QQ(t)), "a": int(a), "b": int(b),
            "D": int(D), "M": int(M), "A": A, "B": B,
            "elapsed_seconds": time.monotonic()-start,
        }

    reason = None
    restrictive_k = False
    if generator == "squareclass":
        work = enumerate(signed_squareclasses(factor["primes"]))
    else:
        work = enumerate(x for n in range(1, x_abs_max+1) for x in (n, -n))

    for index, value in work:
        if (cancelled is not None and cancelled()) or time.monotonic() >= deadline:
            reason = "cancelled" if cancelled is not None and cancelled() else "run_timeout"
            if checkpoint is not None:
                checkpoint({"index": index, "k": None, "z": 1,
                            "examined": examined, "points": records,
                            "factor": factor, "mode": generator})
            break
        if generator == "squareclass":
            d = int(value)
            absolute_k = math.isqrt(x_abs_max // abs(d))
            if k_max and k_max < absolute_k:
                restrictive_k = True
            k_limit = min(absolute_k, k_max) if k_max else absolute_k
            k_values = range(1, k_limit+1)
        else:
            d = None
            k_values = (None,)
        for k in k_values:
            X = d*k*k if d is not None else int(value)
            z_begin = 1
            if index < int(resume.get("index") or 0):
                continue
            if index == int(resume.get("index") or 0):
                prior_k = resume.get("k")
                if prior_k is not None and k is not None and k < int(prior_k):
                    continue
                if prior_k is None or k == prior_k:
                    z_begin = max(1, int(resume.get("z") or 1))
            for Z in range(z_begin, z_max+1):
                if (cancelled is not None and cancelled()) or time.monotonic() >= deadline:
                    reason = "cancelled" if cancelled is not None and cancelled() else "run_timeout"
                    if checkpoint is not None:
                        checkpoint({"index": index, "k": k, "z": Z,
                                    "examined": examined, "points": records,
                                    "factor": factor, "mode": generator})
                    break
                if math.gcd(X, Z) != 1:
                    continue
                if examined_this_attempt >= max_candidates:
                    reason = "candidate_budget"
                    if checkpoint is not None:
                        checkpoint({"index": index, "k": k, "z": Z,
                                    "examined": examined, "points": records,
                                    "factor": factor, "mode": generator})
                    break
                examined += 1
                examined_this_attempt += 1
                Y = _square_candidate(X, Z, A, B, modular_sieve)
                if Y is not None:
                    for rec in _point_records(E, X, Y, Z, d=d, k=k):
                        key = rec["x"], rec["y"]
                        if key not in seen:
                            seen.add(key)
                            records.append(rec)
                    if len(records) >= max_points:
                        reason = "point_budget"
                if checkpoint is not None and (examined % 500 == 0 or reason):
                    checkpoint({"index": index, "k": k, "z": Z+1,
                                "examined": examined, "points": records,
                                "factor": factor, "mode": generator})
                if reason:
                    break
            if reason:
                break
            if checkpoint is not None:
                checkpoint({"index": index+1 if k is None else index,
                            "k": None if k is None else k+1,
                            "z": 1, "examined": examined, "points": records,
                            "factor": factor, "mode": generator})
        if reason:
            break
    if not reason and restrictive_k:
        reason = "k_cap_restricts_x_bound"
    complete = reason is None and (
        (generator == "squareclass" and factor["complete"])
        or (generator == "grid_control" and requested_generator == "grid_control")
    )
    coverage = (
        "bounded_complete" if complete and generator == "squareclass"
        else "grid_bounded_complete" if complete else "bounded_partial"
    )
    return {
        "status": "completed" if complete else "partial",
        "coverage": coverage,
        "reason": reason or ("factor_incomplete_grid_fallback" if requested_generator != generator else None),
        "factor": factor, "points": records, "examined": examined,
        "parameter": str(QQ(t)), "a": int(a), "b": int(b),
        "D": int(D), "M": int(M), "A": A, "B": B,
        "elapsed_seconds": time.monotonic()-start,
    }
