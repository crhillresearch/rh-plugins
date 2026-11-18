"""Integration checks for the two independent rational-cover variants."""
import importlib.util
from pathlib import Path

from sage.all import QQ

from rank42.plugins import read_plugin


ROOT = Path(__file__).resolve().parents[1]
def test_both_variants_specialize_exactly():
    plugin = read_plugin(ROOT)
    assert {variant.id for variant in plugin.variants} == {"cover_4339", "cover_36773"}

    for index in (4339, 36773):
        variant_id = f"cover_{index}"
        spec = importlib.util.spec_from_file_location(
            f"hill_rank18_cover_{index}", ROOT / f"cover_{index}.py"
        )
        family = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(family)
        assert tuple(family.candidate_seed_parameters()) == (0,)
        curve = family.curve(QQ(0))
        assert curve is not None and curve.discriminant() != 0
        assert len(family.generic_section_points(QQ(0))) == 18
        assert family.curve_mod_p(QQ(0), 31).cardinality() == 42
        assert family.validate_generic_rank_claim()["lower_bound"] == 18
