import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_manifest_shape():
    m=json.loads((ROOT/'plugin.json').read_text())
    assert m['schema_version']==1 and m['plugin_type']=='family'
    assert m['id']=='elkies_klagsbrun_z2_rank9_2020'
    assert m['version']=='1.2.4'
    assert m['minimum_rank_hunter_version']=='0.9.2'
    assert m['generic_rank']==9
    assert m['historical_generic_rank_lower']==9
    assert m['generic_rank_claim_state']=='sections_verified'
    assert 'verified_generic_rank_lower' not in m
    assert set(m['capabilities'])=={'candidate_generation','family_search','target_search','known_subgroup','pgl2_search','free_search'}
    assert len(m['variants'])==5
    assert len(m['charts'])==1
    assert m['default_chart']=='published_u11_5'
    chart=m['charts'][0]
    assert chart['variant']=='u11_5_published_chart_search'
    assert chart['native_variant']=='u11_5'
    assert chart['matrix']==['-1','2','1','-6']
    for v in m['variants']:
        assert (ROOT/v['family']['file']).exists()
