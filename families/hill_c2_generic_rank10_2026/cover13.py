"""Hill's rational C2-torsion generic rank-at-least-10 cover #13."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "hill_c2_generic_rank10_common", Path(__file__).with_name("family_common.py"))
common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(common)

generic_rank = 10
parameter_base_genus = 0

def name(): return "Hill C₂ — Generic Rank ≥10 · Cover 13"
def candidate_seed_parameters(): return (0,)
def curve(u): return common.curve(13, u)
def curve_mod_p(u, p): return common.curve_mod_p(13, u, p)
def generic_section_points(u): return common.generic_section_points(13, u)
def generic_section_metadata(u): return common.generic_section_metadata(13, u)
def validate_generic_rank_claim(): return common.validate_generic_rank_claim(13)
def formula_family_data(): return common.formula_family_data(13)
