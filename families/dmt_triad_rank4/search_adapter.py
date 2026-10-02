"""Thin Rank Hunter search adapter for DMT-001 REA CURVE2 / Triad Family."""
from __future__ import annotations
from pathlib import Path

def _family_spec(options):
    spec=str(options.get("family_spec") or "").strip()
    if not spec: raise ValueError("family_spec is required")
    return spec

def _analysis_flags(options):
    flags=["--quick-strategy","pari","--quick-timeout",str(int(options.get("quick_timeout",120))),"--strong-timeout",str(int(options.get("strong_timeout",600))),"--generic-certificate-timeout",str(int(options.get("generic_certificate_timeout",120)))]
    if bool(options.get("quick_only",True)): flags.append("--quick-only")
    if bool(options.get("fast_screen",True)): flags.append("--fast-screen")
    return flags

def build_family_search_command(*,python,db,candidate_file,options):
    cmd=[str(python),"-m","rank42.auto_analyze","--db",str(db),"--input",str(candidate_file),"--family",_family_spec(options),"--limit",str(int(options.get("limit",20)))]
    cmd.extend(_analysis_flags(options)); return cmd

def build_target_search_command(*,python,db,curve_id,options):
    worker=Path(__file__).with_name("target_search.py").resolve()
    if not worker.is_file(): raise ValueError(f"target worker not found: {worker}")
    cmd=[str(python),str(worker),"--db",str(db),"--curve-id",str(int(curve_id)),"--family",_family_spec(options)]
    cmd.extend(_analysis_flags(options)); return cmd
