from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from rank42.plugins import read_plugin, validate_plugin


ROOT = Path(__file__).resolve().parents[1]


def _load_adapter():
    path = ROOT / 'search_adapter.py'
    spec = importlib.util.spec_from_file_location('kloosterman_release_adapter', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_manifest_preserves_historical_only_rank15_contract():
    manifest = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))

    assert manifest['id'] == 'kloosterman_rank15'
    assert manifest['name'] == 'Kloosterman Rank-15 K3'
    assert manifest['version'] == '1.1.0'
    assert manifest['minimum_rank_hunter_version'] == '0.9.2'
    assert manifest['historical_generic_rank_lower'] == 15
    assert manifest['generic_rank_claim_state'] == 'historical_record'
    assert 'verified_generic_rank_lower' not in manifest
    assert 'generic_rank' not in manifest

    provenance = manifest['provenance']
    assert provenance['author'] == 'Remke Kloosterman'
    assert provenance['arxiv'] == 'math/0502439'
    assert provenance['doi'] == '10.4153/CMB-2007-023-2'
    assert provenance['theorem_reference'] == 'Theorem 1.2'
    assert 'rank exactly 15' in provenance['published_claim']
    assert 'different explicit surface' in provenance['abstract_surface_distinction']


def test_family_json_is_exact_theorem_1_2_model_and_has_no_fake_basis():
    family = json.loads((ROOT / 'family.json').read_text(encoding='utf-8'))

    assert family['generic_rank'] is None
    assert family['sections'] == []
    assert family['a_invariants'] == [
        '0',
        '0',
        '0',
        '2*(t^8 + 2*t^4 + 1)',
        '-4*t^2*(t^8 - 6*t^4 + 1)',
    ]


def test_current_core_validates_historical_only_family_and_adapter():
    plugin = read_plugin(ROOT)
    result = validate_plugin(plugin, import_science=True)

    assert result['status'] == 'ready'
    assert result['plugin_version'] == '1.1.0'
    assert result['default_variant'] == 'default'
    assert result['family_name'] == 'Kloosterman explicit elliptic K3, rank 15 over Q(t)'
    assert result['family_generic_rank'] is None
    assert result['validation_parameter'] == '2'
    assert result['validation_discriminant_nonzero'] is True
    assert result['adapter_contract']['api_version'] == 1
    assert 'generic_rank_certificate' not in result['variants'][0]


def test_family_search_explicitly_disables_generic_witness_promotion():
    adapter = _load_adapter()
    cmd = adapter.build_family_search_command(
        python='python',
        db='rank42.db',
        candidate_file='candidates.jsonl',
        options={'limit': 7, 'primary_strategy': 'pari', 'quick_timeout': 45},
    )

    assert '-m' in cmd and 'rank42.auto_analyze' in cmd
    assert '--quick-only' in cmd
    assert '--fast-screen' in cmd
    assert '--no-generic-witness' in cmd
    assert cmd[cmd.index('--limit') + 1] == '7'
    assert cmd[cmd.index('--quick-strategy') + 1] == 'pari'
    assert cmd[cmd.index('--quick-timeout') + 1] == '45'


def test_target_search_uses_current_fixed_curve_contract():
    adapter = _load_adapter()
    cmd = adapter.build_target_search_command(
        python='python',
        db='rank42.db',
        curve_id=123,
        options={
            'stages': '1000,10000',
            'timeout': 30,
            'exact_candidates': 9,
            'certificate_timeout': 150,
        },
    )

    assert '-m' in cmd and 'rank42.fixed_curve_search' in cmd
    assert cmd[cmd.index('--curve-id') + 1] == '123'
    assert cmd[cmd.index('--stages') + 1] == '1000,10000'
    assert cmd[cmd.index('--timeout') + 1] == '30'
    assert cmd[cmd.index('--exact-candidates') + 1] == '9'
    assert cmd[cmd.index('--certificate-timeout') + 1] == '150'


def test_release_readme_is_portable_and_does_not_overclaim():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')

    assert 'Rank Hunter **0.9.2**' in readme
    assert 'Theorem 1.2' in readme
    assert 'historical_generic_rank_lower = 15' in readme
    assert 'with no `verified_generic_rank_lower`' in readme
    assert '--no-generic-witness' in readme
    assert 'PYTHONPATH="${RANK_HUNTER_ROOT}" sage -python' in readme

    assert '/home/' not in readme
    assert '/Users/' not in readme
    assert 'miniforge3' not in readme
    assert 'v0.8.7.1' not in readme
