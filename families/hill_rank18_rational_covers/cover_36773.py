"""Hill rational quadratic cover 36773."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("hill_rank18_cover_common_36773", Path(__file__).with_name("family_common.py"))
common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(common)

generic_rank = 18
parameter_base_genus = 0

def name(): return "Hill rank ≥18 rational cover 36773"
def candidate_seed_parameters(): return (0,)
def curve(u): return common.curve(36773, u)
def curve_mod_p(u, p): return common.curve_mod_p(36773, u, p)
def generic_section_points(u): return common.generic_section_points(36773, u)
def generic_section_metadata(u): return common.generic_section_metadata(36773, u)
def validate_generic_rank_claim(): return common.validate_generic_rank_claim(36773)
