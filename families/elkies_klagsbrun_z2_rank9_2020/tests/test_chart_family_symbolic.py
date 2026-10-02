import json
from pathlib import Path
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
FAM=ROOT/'families'


def expr(text,var):
    return sp.sympify(text.replace('^','**'),locals={'t':var})


def test_published_search_model_is_exact_native_substitution():
    native=json.loads((FAM/'u11_5.json').read_text())
    chart=json.loads((FAM/'u11_5_published_chart_search.json').read_text())
    t,s=sp.symbols('t s')
    M=(2-s)/(s-6)
    for a,b in zip(native['a_invariants'],chart['a_invariants']):
        assert sp.cancel(expr(a,t).subs(t,M)-expr(b,s))==0
    assert len(native['sections'])==len(chart['sections'])==9
    for pn,pc in zip(native['sections'],chart['sections']):
        assert sp.cancel(expr(pn['x'],t).subs(t,M)-expr(pc['x'],s))==0
        assert sp.cancel(expr(pn['y'],t).subs(t,M)-expr(pc['y'],s))==0
