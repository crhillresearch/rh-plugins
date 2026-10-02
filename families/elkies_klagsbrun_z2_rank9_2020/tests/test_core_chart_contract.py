from fractions import Fraction
from pathlib import Path

from rank42.plugins import read_plugin, get_chart

ROOT=Path(__file__).resolve().parents[1]


def test_core_reads_exact_published_chart():
    plugin=read_plugin(ROOT)
    assert plugin.id=='elkies_klagsbrun_z2_rank9_2020'
    assert 'pgl2_search' in plugin.capabilities
    chart=get_chart(plugin,'published_u11_5')
    assert chart.variant_id=='u11_5_published_chart_search'
    assert chart.native_variant_id=='u11_5'
    s=Fraction(-68559,326291)
    t=chart.forward(s)
    assert t==Fraction(-721141,2026305)
    assert chart.inverse(t)==s
