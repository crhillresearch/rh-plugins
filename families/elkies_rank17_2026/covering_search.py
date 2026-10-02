"""Hard-timeout orchestration for classical Elkies 2-covering searches."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKER = HERE / "covering_worker.py"
MARKER = "RANK42_ELKIES_COVERING_WORKER="


class CoveringSearchTimeout(RuntimeError):
    pass


class CoveringSearchFailure(RuntimeError):
    pass


def run_covering_worker(
    a_invariants,
    known_points,
    *,
    mode,
    timeout,
    first_limit=20,
    second_limit=10,
    n_aux=-1,
    lim1=5,
    lim3=80,
    limtriv=3,
    maxprob=20,
    limbigprime=30,
):
    payload = {
        "mode": str(mode),
        "a_invariants": [str(x) for x in a_invariants],
        "known_points": [[str(P[0]), str(P[1])] for P in known_points],
        "first_limit": int(first_limit),
        "second_limit": int(second_limit),
        "n_aux": int(n_aux),
        "lim1": int(lim1),
        "lim3": int(lim3),
        "limtriv": int(limtriv),
        "maxprob": int(maxprob),
        "limbigprime": int(limbigprime),
    }
    started = time.monotonic()
    try:
        cp = subprocess.run(
            [sys.executable, str(WORKER)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=max(1, int(timeout)),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CoveringSearchTimeout(
            f"{mode} classical covering search exceeded {int(timeout)}s"
        ) from exc

    runtime = time.monotonic() - started
    marker_line = None
    for line in reversed((cp.stdout or "").splitlines()):
        if line.startswith(MARKER):
            marker_line = line[len(MARKER):]
            break
    tail = "\n".join(((cp.stdout or "") + "\n" + (cp.stderr or "")).splitlines()[-40:])
    if marker_line is None:
        raise CoveringSearchFailure(
            f"{mode} worker returned no result marker (exit={cp.returncode}); tail:\n{tail}"
        )
    try:
        result = json.loads(marker_line)
    except json.JSONDecodeError as exc:
        raise CoveringSearchFailure(f"{mode} worker returned invalid JSON; tail:\n{tail}") from exc
    result["runtime_seconds"] = runtime
    result["worker_exit_code"] = int(cp.returncode)
    if result.get("status") == "error":
        raise CoveringSearchFailure(result.get("error") or tail)
    if cp.returncode != 0:
        raise CoveringSearchFailure(
            f"{mode} worker exited {cp.returncode} after emitting result; tail:\n{tail}"
        )
    return result
