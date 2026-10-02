"""DMT-001 Triad Family variant CEF."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TRIPLE = "cef"
generic_rank = 4
historical_generic_rank_lower = 4

# Candidate-scoring arithmetic is owned by TRIPLE + _family_common.curve_mod_p.
# Certificate bundles below do not change the finite-field Nagao tables.
nagao_cache_identity = "dmt-triad-cef-finite-field-v1"
nagao_cache_legacy_keys = (
    "plugin-cef_family-162ccd7039e1c862",
    "plugin-cef_family-42a5d9557a9ab9d5",
)

def _load_common():
    path = Path(__file__).with_name("_family_common.py")
    spec = importlib.util.spec_from_file_location(f"rank42_dmt_triad_common_{TRIPLE}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_common = _load_common()

def name():
    return f"DMT Triad Family - {TRIPLE.upper()}"

def curve(t):
    return _common.curve(TRIPLE, t)

def curve_mod_p(r, p):
    return _common.curve_mod_p(TRIPLE, r, p)

def generic_section_points(t):
    return _common.generic_section_points(TRIPLE, t)

def construction_check(t="12/5"):
    return _common.construction_check(TRIPLE, t)

def validate_generic_rank_claim():
    return _common.validate_generic_rank_claim(TRIPLE)


def _load_rank10_certificate():
    path = Path(__file__).with_name("cef_rank10_certificate.py")
    spec = importlib.util.spec_from_file_location("rank42_dmt_triad_cef_rank10", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_rank10 = _load_rank10_certificate()


def _load_historical_highrank():
    path = Path(__file__).with_name("cef_historical_highrank.py")
    spec = importlib.util.spec_from_file_location(
        "rank42_dmt_triad_cef_historical_highrank", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_historical_highrank = _load_historical_highrank()
_historical_model_index = None


def _model_key(E):
    if E is None:
        return None
    return tuple(str(a) for a in E.a_invariants())


def _historical_index():
    global _historical_model_index
    if _historical_model_index is not None:
        return _historical_model_index
    out = {}
    for record in _historical_highrank.RECORDS:
        source_E = curve(record["source_parameter"])
        key = _model_key(source_E)
        if key is not None:
            out[key] = record
    _historical_model_index = out
    return out


def _certificate_record(t):
    E = curve(t)
    if E is None:
        return None, None, None
    key = _model_key(E)
    rank10_E = curve(str(_rank10.SOURCE_PARAMETER))
    if key == _model_key(rank10_E):
        return "rank10", E, None
    record = _historical_index().get(key)
    if record is not None:
        return "historical", E, record
    return None, E, None


def certified_specialization_points(t):
    from sage.all import QQ

    kind, E, record = _certificate_record(t)
    if E is None or kind is None:
        return []
    if kind == "rank10":
        return [E(QQ(x), QQ(y)) for x, y in _rank10.POINTS]

    points = list(generic_section_points(t))
    for x, y in record["extra_points"]:
        points.append(E(QQ(x), QQ(y)))
    return points


def certified_specialization_metadata(t):
    from sage.all import QQ

    kind, E, record = _certificate_record(t)
    if E is None or kind is None:
        return {}
    requested = str(QQ(t))
    if kind == "rank10":
        meta = dict(_rank10.metadata(str(_rank10.SOURCE_PARAMETER)))
        meta["requested_parameter"] = requested
        meta["matched_by_exact_model"] = True
        return meta

    return {
        "source": record["source"],
        "family": "cef",
        "source_parameter": record["source_parameter"],
        "requested_parameter": requested,
        "external_exact_rank_claim": int(record["exact_rank_claim"]),
        "generic_section_count": 4,
        "off_baseline_point_count": len(record["extra_points"]),
        "bundle_point_count": 4 + len(record["extra_points"]),
        "workflow_run_id": int(record["workflow_run_id"]),
        "artifact_id": int(record["artifact_id"]),
        "source_commit": record["source_commit"],
        "artifact_sha256": record["artifact_sha256"],
        "matched_by_exact_model": True,
        "proof_policy": (
            "historical rank/artifact metadata is scheduling provenance only; "
            "Rank Hunter independently exact-certifies the combined point bundle"
        ),
    }
