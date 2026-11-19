"""Search command construction for a JSON family plugin."""
from __future__ import annotations

import json
from pathlib import Path

def adapter_for_plugin(plugin_root):
    root = Path(plugin_root).resolve()
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    variant = next(
        (item for item in manifest.get("variants", [])
         if item.get("id") == manifest.get("default_variant")),
        (manifest.get("variants") or [{}])[0],
    )
    family_def = variant.get("family") or manifest.get("family") or {}
    family_file = root / str(family_def.get("file") or "family.json")
    runner = root / "search_runner.py"
    family_name = str(variant.get("curve_family_name") or manifest.get("name") or "")
    plugin_id = str(manifest.get("id") or root.name)

    def search_options(*, context="family", **_kwargs):
        if context not in {"family", "target"}:
            raise ValueError(f"unsupported search option context: {context!r}")
        return [dict(option) for option in manifest["search_options"][context]]

    def command(*, python, db, mode, source_flag, source_value, options):
        defaults = {
            "family": {"stages": "1000,10000,100000", "timeout": 20,
                       "max_points": 32, "model_prep_timeout": 10},
            "target": {"stages": "1000,10000,100000,1000000", "timeout": 30,
                       "max_points": 64, "model_prep_timeout": 15},
        }[mode]
        cmd = [
            str(python), str(runner), "--db", str(db), "--mode", mode,
            source_flag, str(source_value), "--family-file", str(family_file),
            "--family-name", family_name, "--plugin-id", plugin_id,
            "--stages", str(options.get("stages") or defaults["stages"]),
            "--timeout", str(max(1, min(3600, int(options.get("timeout", defaults["timeout"]))))),
            "--max-points", str(max(0, min(2000, int(options.get("max_points", 0))))),
            "--model-prep-timeout", str(max(0, min(600, int(options.get("model_prep_timeout", 10))))),
        ]
        if options.get("ratpoints"):
            cmd.extend(["--ratpoints", str(options["ratpoints"])])
        return cmd

    def build_family_search_command(*, python, db, candidate_file, options):
        return command(
            python=python, db=db, mode="family", source_flag="--input",
            source_value=candidate_file, options=options,
        )

    def build_target_search_command(*, python, db, curve_id, options):
        return command(
            python=python, db=db, mode="target", source_flag="--curve-id",
            source_value=int(curve_id), options=options,
        )

    return {
        "search_options": search_options,
        "build_family_search_command": build_family_search_command,
        "build_target_search_command": build_target_search_command,
    }
