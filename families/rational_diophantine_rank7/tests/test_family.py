import sys
from pathlib import Path
import pytest
pytest.importorskip("sage.all")
from sage.all import QQ

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import family

EXPECTED_X = ["38540677847903454008558223360000","178922409809838644555667210240000","72051389475320867247399895040000","66579605091474988619076835737600","13362426543070313045072805888000","126710845595682509808491456102400","2179385680764224839490312601600"]

def test_control_reconstructs_paper_base_pair_curve_and_seven_points():
    lift=family.rank7_base_lift(26)
    assert lift["z"]==QQ(16120)
    assert lift["w2"]==QQ(-76)/3
    assert family._condition8(lift["w2"],QQ(26))==0
    c=family.construction_check(26)
    assert c["sections"]==7
    assert c["distinct_nonzero"]==7
    assert c["torsion_invariants"]==[2,2]
    assert c["a_invariants"]==[
        "0",
        "-163531808801344950045916528640000",
        "0",
        "6680706316011654681276493655189069731350803361465165152256000000",
        "0",
    ]
    assert c["x_coordinates"]==EXPECTED_X

@pytest.mark.parametrize("w3",[-234,-30,-18,26,42,94,QQ(-202)/3,QQ(-182)/3,QQ(-14)/3])
def test_paper_sample_rank7_base_values_reconstruct_seven_points(w3):
    E=family.curve(w3)
    assert E is not None
    assert len(family.generic_section_points(w3))==7

def test_non_base_parameter_is_rejected_exactly():
    assert family.curve(0) is None
    with pytest.raises(ArithmeticError):
        family.rank7_base_lift(0)

def test_exact_generic_lower_bound_seven():
    c=family.validate_generic_rank_claim()
    assert c["verified"] is True
    assert c["lower_bound"]>=7
    assert c["details"]["control_parameter"]=="26"
    assert c["details"]["control_w2"]=="-76/3"
    assert c["details"]["exact_generic_rank_claimed"] is False

def test_finite_field_candidate_model_uses_local_base_square_filter():
    seen_good=False
    seen_rejected=False
    for r in range(101):
        E=family.curve_mod_p(r,101)
        if E is None:
            seen_rejected=True
        else:
            seen_good=True
    assert seen_good and seen_rejected
