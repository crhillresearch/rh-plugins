"""Variant-aware exact searches using the standard JSON-family runner."""
from pathlib import Path
import json
import sys
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from search_support import adapter_for_plugin

ROOT = Path(__file__).resolve().parent
_adapter = adapter_for_plugin(ROOT)
search_options = _adapter['search_options']

def _build(method, options, **kwargs):
    manifest = json.loads((ROOT / 'plugin.json').read_text())
    variant_id = options.get('plugin_variant') or manifest['default_variant']
    variants = {v['id']: v for v in manifest['variants']}
    if variant_id not in variants:
        raise ValueError(f'Unknown family variant: {variant_id}')
    variant = variants[variant_id]
    command = _adapter[method](options=options, **kwargs)
    command[command.index('--family-file') + 1] = str(ROOT / variant['family']['file'])
    command[command.index('--family-name') + 1] = variant['name']
    return command

def build_family_search_command(*, python, db, candidate_file, options):
    return _build('build_family_search_command', options, python=python, db=db, candidate_file=candidate_file)

def build_target_search_command(*, python, db, curve_id, options):
    return _build('build_target_search_command', options, python=python, db=db, curve_id=curve_id)
