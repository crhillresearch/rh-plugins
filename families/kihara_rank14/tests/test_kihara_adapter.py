from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load_adapter():
    spec = spec_from_file_location("kihara_adapter_test", ROOT / "search_adapter.py")
    mod = module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_adapter_uses_plugin_local_worker():
    mod = load_adapter()
    cmd = mod.build_target_search_command(
        python="python", db="rank42.db", curve_id=7,
        options={"charts": 12, "stages": "1000,10000", "certificate_timeout": 90},
    )
    assert Path(cmd[1]).resolve() == (ROOT / "chart_search.py").resolve()
    assert not any("rank42.kihara" in piece for piece in cmd)
    assert "--id" in cmd and "7" in cmd
    assert "--certificate-timeout" in cmd and "90" in cmd


def test_search_options_are_declarative_for_both_contexts():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["search_options"]["family"]
    assert manifest["search_options"]["target"]
