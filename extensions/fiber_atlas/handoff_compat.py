"""Compatibility handoff shim for older Rank Hunter cores.

Current Rank Hunter owns these helpers in rank42.ui_handoffs.  Fiber Atlas
loads this file only when that core module does not exist, so older research
checkouts can still render and route the Workspace against their existing data.

The shim is navigation/context only. It does not launch jobs or modify
scientific database state.
"""
from __future__ import annotations

import hashlib
import json


RESEARCH_HANDOFF_KEY = "_rh_research_handoff"
RESEARCH_HANDOFF_VERSION = 1


def _positive_int(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _json_copy(value):
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":")))


def normalize_research_handoff(payload):
    if not isinstance(payload, dict):
        raise ValueError("research handoff must be a mapping")

    source = str(payload.get("source") or "").strip()
    kind = str(payload.get("kind") or "").strip()
    family = str(payload.get("family") or "").strip()
    if not source:
        raise ValueError("research handoff source is required")
    if not kind:
        raise ValueError("research handoff kind is required")

    curve_ids = []
    seen = set()
    for raw in payload.get("curve_ids") or ():
        curve_id = _positive_int(raw)
        if curve_id is None or curve_id in seen:
            continue
        seen.add(curve_id)
        curve_ids.append(curve_id)

    parameters = []
    for rec in payload.get("parameters") or ():
        if not isinstance(rec, dict):
            continue
        curve_id = _positive_int(rec.get("curve_id"))
        parameter = str(rec.get("parameter") or "").strip()
        if curve_id is None or not parameter:
            continue
        item = {"curve_id": curve_id, "parameter": parameter}
        for key in (
            "rigorous_lower",
            "generic_lower",
            "family_baseline",
            "family_baseline_kind",
            "baseline_excess",
            "rank_jump",
            "score",
            "root_number",
        ):
            if rec.get(key) is not None:
                item[key] = rec.get(key)
        parameters.append(item)

    selection = payload.get("selection")
    if selection is None:
        selection = {}
    if not isinstance(selection, dict):
        raise ValueError("research handoff selection must be a mapping")

    normalized = {
        "version": RESEARCH_HANDOFF_VERSION,
        "source": source,
        "kind": kind,
        "family": family,
        "curve_ids": curve_ids,
        "parameters": parameters,
        "selection": _json_copy(selection),
    }
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    normalized["selection_hash"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    return normalized


def _store(state, payload):
    normalized = normalize_research_handoff(payload)
    state[RESEARCH_HANDOFF_KEY] = normalized
    return normalized


def route_curve_to_target(state, curve_id, *, handoff=None):
    curve_id = _positive_int(curve_id)
    if curve_id is None:
        raise ValueError("target curve id must be a positive integer")
    # Newer cores read the semantic key; older cores read target_curve_id.
    state["analysis_active_curve_id"] = curve_id
    state["target_curve_id"] = curve_id
    if handoff is not None:
        _store(state, handoff)
    state["rh_page"] = "Target"
    return curve_id


def route_selection_to_pipelines(state, handoff):
    payload = _store(state, handoff)
    state["builder_main_view"] = "Editor"
    state["builder_view_revision"] = int(
        state.get("builder_view_revision") or 0
    ) + 1
    state["rh_page"] = "Pipelines"
    return payload
