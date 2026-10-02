from fractions import Fraction
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("dmt_triad_math_test",ROOT/"triad_math.py")
M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)

def test_paper_control_fiber_and_selected_triads():
    t=Fraction(12,5); values=M.piezas_values(t)
    assert M.good_selected_fiber(t)
    assert M.is_diophantine_sextuple(values)
    assert M.verify_paper_regularity(values)
    assert M.SELECTED_TRIPLES==("ace","acf","bde","bdf","bef","cef")

def test_each_triad_has_full_rational_two_torsion_and_four_exact_sections():
    t=Fraction(12,5); values=M.piezas_values(t)
    for triple in M.SELECTED_TRIPLES:
        roots=M.split_roots(values,triple)
        assert len(set(roots))==3
        points=M.paper_section_coordinates(t,triple)
        assert len(points)==4
        assert len(set(points))==4
        for x,y in points:
            assert y*y==M.curve_rhs(values,triple,x)

def test_section_label_table_matches_dmt_rank_jumps_source():
    assert M.PAPER_SECTIONS=={
        "ace":("P","R","E_d","E_f"),
        "acf":("P","R","E_d","E_e"),
        "bde":("P","R","E_c","E_f"),
        "bdf":("P","R","E_c","E_e"),
        "bef":("P","R","E_c","E_d"),
        "cef":("P","R","E_a","E_b"),
    }

def test_a_invariants_expand_the_split_cubic():
    values=M.piezas_values(Fraction(12,5))
    for triple in M.SELECTED_TRIPLES:
        u,v,w=M.triple_values(values,triple)
        a1,a2,a3,a4,a6=M.curve_a_invariants(values,triple)
        assert a1==0 and a3==0
        assert a2==u*v+u*w+v*w
        assert a4==(u*v)*(u*w)+(u*v)*(v*w)+(u*w)*(v*w)
        assert a6==(u*v)*(u*w)*(v*w)
