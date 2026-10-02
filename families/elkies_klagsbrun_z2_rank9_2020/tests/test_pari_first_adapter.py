from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]


def adapter():
    spec = importlib.util.spec_from_file_location('ek_adapter_pari', ROOT / 'search_adapter.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_family_search_defaults_to_pari_and_strong_certificate_timeout():
    a = adapter()
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    opts = manifest["search_options"]["family"]
    quick = next(x for x in opts if x['key'] == 'quick_strategy')
    assert quick['default'] == 'pari'
    assert quick['choices'][0] == 'pari'
    assert 'PARI' in quick['label']
    assert any(x['key'] == 'strong_certificate_timeout' for x in opts)

    cmd = a.build_family_search_command(
        python='/sage/python', db='/tmp/rank42.db', candidate_file='/tmp/c.jsonl',
        options={'family_spec': 'json:/tmp/family.json', 'limit': 2},
    )
    joined = ' '.join(cmd)
    assert '--quick-strategy pari' in joined
    assert '--strong-certificate-timeout 120' in joined


def test_explicit_mwrank_override_remains_available():
    a = adapter()
    cmd = a.build_family_search_command(
        python='/sage/python', db='/tmp/rank42.db', candidate_file='/tmp/c.jsonl',
        options={
            'family_spec': 'json:/tmp/family.json',
            'quick_strategy': 'mwrank',
            'strong_certificate_timeout': 77,
        },
    )
    joined = ' '.join(cmd)
    assert '--quick-strategy mwrank' in joined
    assert '--strong-certificate-timeout 77' in joined
