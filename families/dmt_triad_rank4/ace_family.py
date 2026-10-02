"""DMT-001 Triad Family variant ACE."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TRIPLE = "ace"
generic_rank = 4
historical_generic_rank_lower = 4

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
