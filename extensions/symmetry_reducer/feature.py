"""Runtime search-command hook for the Symmetry Reducer Feature plugin.

v2.1 understands the PGL2 workers used by Campbell, Kihara and
Mestre/Fermigier.  The family plugins remain unmodified; enabled Feature hooks
wrap their adapter-built command immediately before launch.
"""
from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRAPPER = HERE / "search_wrapper.py"

_SUPPORTED_MODULES = {
    "plugins.campbell1999_rank13.campbell_chart_search": ({"campbell1999_rank13"}, "campbell"),
    "plugins.kihara2001.chart_search": ({"kihara2001_rank14"}, "kihara"),
    "rank42.kihara_chart_search": ({"kihara2001_rank14"}, "kihara"),
    "plugins.mestre_sextuple.chart_search": ({"mestre_sextuple_rank11"}, "mestre"),
    "rank42.mestre_chart_search": ({"mestre_sextuple_rank11", "fermigier_rank12_exact"}, "mestre"),
    "plugins.fermigier_rank12_exact.chart_search": ({"fermigier_rank12_exact"}, "mestre"),
}


def _arg_value(command, flag):
    try:
        i = command.index(flag)
    except ValueError:
        return None
    return command[i + 1] if i + 1 < len(command) else None


def _script_worker(value):
    p = Path(str(value))
    name = p.name
    parts = set(p.parts)
    if name == "campbell_chart_search.py":
        return {"campbell1999_rank13"}, "campbell"
    if name in {"chart_search.py", "kihara_chart_search.py"} and any("kihara" in part for part in parts):
        return {"kihara2001_rank14"}, "kihara"
    if name in {"chart_search.py", "mestre_chart_search.py"} and any("mestre" in part or "fermigier" in part for part in parts):
        return {"mestre_sextuple_rank11", "fermigier_rank12_exact"}, "mestre"
    return None


def _detect_worker(command):
    """Return worker descriptor or None.

    Descriptor keys: family_id, family_kind, invocation, worker_index, value.
    ``worker_index`` points to the script path for script invocation and to the
    ``-m`` token for module invocation.
    """
    for i in range(1, len(command) - 1):
        if command[i] == "-m":
            module = str(command[i + 1])
            rec = _SUPPORTED_MODULES.get(module)
            if rec:
                family_ids, family_kind = rec
                return {
                    "family_ids": set(family_ids),
                    "family_kind": family_kind,
                    "invocation": "module",
                    "worker_index": i,
                    "value": module,
                    "args_index": i + 2,
                }

    for i, value in enumerate(command[1:], 1):
        rec = _script_worker(value)
        if rec:
            family_ids, family_kind = rec
            return {
                "family_ids": set(family_ids),
                "family_kind": family_kind,
                "invocation": "script",
                "worker_index": i,
                "value": str(value),
                "args_index": i + 1,
            }
    return None


def _plan_mode(family_kind):
    """Choose conservative default policy.

    ``dedup`` preserves the selected chart pool modulo exact source symmetry and
    is the validation-safe default for all families.  ``refill`` is implemented
    in the wrapper and can be enabled without changing family code by starting
    Rank Hunter with ``RANK42_SYMMETRY_PLAN_MODE=refill``.  It generates farther
    down the ranked pool until the requested number of distinct symmetry-orbit
    representatives is reached (or the planner exhausts its candidates).
    """
    requested = str(os.environ.get("RANK42_SYMMETRY_PLAN_MODE") or "").strip().lower()
    if requested in {"dedup", "refill"}:
        return requested
    return "dedup"


def on_search_command(context):
    """Wrap supported exact PGL2 searches without editing family plugins."""
    family = context.get("family_plugin") or {}
    command = [str(x) for x in (context.get("command") or [])]
    if len(command) < 2:
        return None

    worker = _detect_worker(command)
    if worker is None:
        return None

    # When family provenance is available it must agree with the worker.  The
    # worker fallback remains useful for sparse target-search metadata.
    family_id = str(family.get("id") or "")
    if family_id and family_id not in worker["family_ids"]:
        return None

    args = command[worker["args_index"]:]
    family_kind = worker["family_kind"]

    if family_kind == "kihara":
        # Kihara's chart worker is rational-only; there is no --mode option.
        mode = "rational"
    else:
        mode = (_arg_value(args, "--mode") or "both").lower()

    include_controls = "--include-known-fibers" in args
    allow_inversion = mode == "rational" and not include_controls
    plan_mode = _plan_mode(family_kind)

    prefix = command[:worker["worker_index"]]
    wrapper_args = [
        str(WRAPPER),
        "--family-kind", family_kind,
        "--plan-mode", plan_mode,
    ]
    if worker["invocation"] == "module":
        wrapper_args += ["--original-module", worker["value"]]
    else:
        wrapper_args += ["--original-script", worker["value"]]
    replacement = prefix + wrapper_args + ["--"] + args

    return {
        "command": replacement,
        "note": f"exact PGL2 source-height symmetry ({family_kind}, {plan_mode}) enabled",
        "metadata": {
            "family_plugin_id": family_id or sorted(worker["family_ids"])[0],
            "family_kind": family_kind,
            "mode": mode,
            "allow_inversion": allow_inversion,
            "plan_mode": plan_mode,
            "wrapper": str(WRAPPER),
        },
    }
