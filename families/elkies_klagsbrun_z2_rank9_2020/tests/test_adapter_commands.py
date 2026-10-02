from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]


def adapter():
    spec=importlib.util.spec_from_file_location('ek_adapter',ROOT/'search_adapter.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_family_search_uses_core_generic_section_path():
    a=adapter()
    cmd=a.build_family_search_command(python='/sage/python',db='/tmp/rank42.db',candidate_file='/tmp/c.jsonl',options={
        'family_spec':'json:/tmp/family.json','limit':3,'fast_screen':True,'generic_certificate_timeout':77
    })
    joined=' '.join(cmd)
    assert '-m rank42.auto_analyze' in joined
    assert '--generic-certificate-timeout 77' in joined
    assert '--no-generic-witness' not in cmd


def test_target_search_uses_core_rigorous_point_ledger():
    a=adapter()
    cmd=a.build_target_search_command(python='/sage/python',db='/tmp/rank42.db',curve_id=12,options={
        'stages':'1000,10000','timeout':30,'exact_candidates':6,'certificate_timeout':90,'ratpoints':'/opt/ratpoints_gpu'
    })
    joined=' '.join(cmd)
    assert '-m rank42.fixed_curve_search' in joined
    assert '--exact-candidates 6' in joined
    assert '--ratpoints /opt/ratpoints_gpu' in joined
