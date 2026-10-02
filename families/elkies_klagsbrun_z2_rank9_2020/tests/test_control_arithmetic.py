from fractions import Fraction
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def q(s): return Fraction(str(s))
def M(s): s=q(s); return (q(2)-s)/(s-q(6))
def test_chart_controls():
    c=json.loads((ROOT/'data/published_controls.json').read_text())
    r20=c['rank20']; assert M(r20['derived_chart_parameter_consistent_with_native_map'])==q(r20['native_parameter'])
    assert M(r20['published_chart_parameter_printed'])!=q(r20['native_parameter'])
    r19=c['rank19_u11_5']; assert M(r19['published_chart_parameter'])==q(r19['native_parameter'])
