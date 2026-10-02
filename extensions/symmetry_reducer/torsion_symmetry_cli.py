#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def _load_local_engine():
    import importlib.util
    module_name="rank42_extension_torsion_symmetry_reducer_engine_cli"
    module=sys.modules.get(module_name)
    if module is not None: return module
    path=HERE/"engine.py"
    spec=importlib.util.spec_from_file_location(module_name,path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load Torsion Symmetry backend: {path}")
    module=importlib.util.module_from_spec(spec)
    sys.modules[module_name]=module
    spec.loader.exec_module(module)
    return module

_engine=_load_local_engine()
audit_weierstrass_2torsion=_engine.audit_weierstrass_2torsion
chart_audit_from_payload=_engine.chart_audit_from_payload
load_json=_engine.load_json
recover_pgl2_from_samples=_engine.recover_pgl2_from_samples

def main():
    ap=argparse.ArgumentParser(description="Exact torsion/PGL2 search-symmetry audit")
    sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("audit-weierstrass"); a.add_argument("--curve",required=True)
    r=sub.add_parser("recover-action"); r.add_argument("--samples",required=True)
    c=sub.add_parser("reduce-charts"); c.add_argument("--charts",required=True); c.add_argument("--actions",required=True); c.add_argument("--coordinate",default="native-x")
    args=ap.parse_args()
    if args.cmd=="audit-weierstrass":
        out=audit_weierstrass_2torsion(load_json(args.curve))
    elif args.cmd=="recover-action":
        data=load_json(args.samples); out=recover_pgl2_from_samples(data.get("samples") if isinstance(data,dict) else data)
    else:
        out=chart_audit_from_payload(load_json(args.charts),load_json(args.actions),coordinate_label=args.coordinate)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
