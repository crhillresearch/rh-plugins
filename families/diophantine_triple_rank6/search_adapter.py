"""Family/Target adapter for the Dujella-Peral rank-6 Diophantine family."""
from __future__ import annotations
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUNNER=HERE/"search_runner.py"

def search_options(*,context="family",**_kwargs):
    if context not in {"family","target"}:
        raise ValueError(f"unsupported search option context: {context!r}")
    return [dict(r) for r in json.loads((HERE/"plugin.json").read_text(encoding="utf-8"))["search_options"][context]]

def _command(*,python,db,mode,source_flag,source_value,options):
    cmd=[str(python),str(RUNNER),"--db",str(db),"--mode",str(mode),str(source_flag),str(source_value),
         "--stages",str(options.get("stages") or ("1000,10000,100000" if mode=="family" else "1000,10000,100000,1000000")),
         "--timeout",str(int(options.get("timeout",20 if mode=="family" else 30))),
         "--max-points",str(int(options.get("max_points",32 if mode=="family" else 64))),
         "--model-prep-timeout",str(int(options.get("model_prep_timeout",10 if mode=="family" else 15)))]
    if options.get("include_generic",True):
        cmd.append("--include-generic")
    if options.get("ratpoints"):
        cmd += ["--ratpoints",str(options["ratpoints"])]
    return cmd

def build_family_search_command(*,python,db,candidate_file,options):
    return _command(python=python,db=db,mode="family",source_flag="--input",source_value=candidate_file,options=options)

def build_target_search_command(*,python,db,curve_id,options):
    return _command(python=python,db=db,mode="target",source_flag="--curve-id",source_value=int(curve_id),options=options)
