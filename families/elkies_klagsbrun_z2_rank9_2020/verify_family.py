from __future__ import annotations
import json
from pathlib import Path
from sage.all import QQ, EllipticCurve
from rank42.formula_family import FormulaFamily
from rank42.plugins import read_plugin, get_chart

ROOT=Path(__file__).resolve().parent


def q(s):
    return QQ(str(s))


def main():
    controls=json.loads((ROOT/'data/published_controls.json').read_text())
    files=['u11_5','u2_5','u2_13','u22_13','u11_5_published_chart_search']
    for stem in files:
        fam=FormulaFamily.from_json(ROOT/'families'/f'{stem}.json')
        report=fam.validate_symbolically()
        assert report['sections_verified_on_curve']==9
        E=fam.curve(QQ(0)); assert E is not None and E(QQ(0),QQ(0)).order()==2
        print(f'[ok] {stem}: 9 symbolic sections; visible 2-torsion')

    plugin=read_plugin(ROOT)
    chart=get_chart(plugin,'published_u11_5')
    c20=controls['rank20']
    s=q(c20['derived_chart_parameter_consistent_with_native_map'])
    native=q(c20['native_parameter'])
    assert q(chart.forward(str(s)))==native
    assert q(chart.inverse(str(native)))==s

    fam=FormulaFamily.from_json(ROOT/'families/u11_5.json')
    E=fam.curve(native); assert E is not None
    Emin=EllipticCurve(QQ,[q(x) for x in c20['minimal_model_a_invariants']])
    assert E.is_isomorphic(Emin)
    assert len(fam.generic_section_points(native))==9
    for x in c20['generator_x_coordinates']:
        assert Emin.lift_x(q(x),all=True), f'published rank-20 x-coordinate does not lift: {x}'

    printed=q(c20['published_chart_parameter_printed'])
    assert q(chart.forward(str(printed)))!=native
    c19=controls['rank19_u11_5']
    assert q(chart.forward(c19['published_chart_parameter']))==q(c19['native_parameter'])

    search=FormulaFamily.from_json(ROOT/'families/u11_5_published_chart_search.json')
    assert search.curve(s).is_isomorphic(E)
    print('[ok] core PGL2 chart maps corrected rank-20 chart parameter exactly to native fiber')
    print('[ok] transformed search family is isomorphic to the native rank-20 specialization')
    print('[ok] rank-20 native model is isomorphic to Appendix B.2 minimal model')
    print('[ok] all 20 published rank-20 generator x-coordinates lift on the Appendix B.2 model')
    print('[ok] published rank-19 chart/native pair round-trips through the same map')


if __name__=='__main__':
    main()
