"""Exact-search adapter for this published family."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from search_support import adapter_for_plugin
_adapter = adapter_for_plugin(Path(__file__).resolve().parent)
search_options = _adapter['search_options']
build_family_search_command = _adapter['build_family_search_command']
build_target_search_command = _adapter['build_target_search_command']
