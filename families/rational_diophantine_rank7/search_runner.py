"""Write-free exact point search for the Dujella-Peral rank>=7 genus-1-base family."""
from __future__ import annotations
import argparse,json,os,sqlite3
from pathlib import Path
from sage.all import EllipticCurve,QQ
import family
from rank42.model_points import map_points_exact
from rank42.model_prep import ModelPrepFailure,ModelPrepTimeout,run_global_minimal_model
from rank42.plugin_geometry_result import RESULT_ENV,SCHEMA
from rank42.ratpoints import RatpointsFailure,RatpointsNotFound,RatpointsTimeout,probe_version,run_ratpoints
from rank42.search_models import completed_square_polynomial,recover_weierstrass_y

ENGINE_VERSION="0.1.0"

def _stages(text):
    vals=sorted({int(x.strip()) for x in str(text).split(",") if x.strip()})
    if not vals or vals[0]<=0:
        raise argparse.ArgumentTypeError("positive comma-separated stages required")
    return vals

def parse_args(argv=None):
    ap=argparse.ArgumentParser(description="Dujella-Peral rank>=7 exact point search")
    ap.add_argument("--db",required=True)
    ap.add_argument("--mode",choices=["family","target"],required=True)
    src=ap.add_mutually_exclusive_group(required=True); src.add_argument("--input"); src.add_argument("--curve-id",type=int)
    ap.add_argument("--stages",type=_stages,default=_stages("1000,10000,100000"))
    ap.add_argument("--timeout",type=int,default=20); ap.add_argument("--ratpoints")
    ap.add_argument("--max-points",type=int,default=32); ap.add_argument("--model-prep-timeout",type=int,default=10)
    ap.add_argument("--include-generic",action="store_true")
    return ap.parse_args(argv)

def _candidate_record(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec=json.loads(line)
            if not isinstance(rec,dict): raise ValueError("candidate input must contain JSON objects")
            return rec
    raise ValueError("candidate input is empty")

def _subject(args):
    con=sqlite3.connect(str(args.db)); con.row_factory=sqlite3.Row
    try:
        if args.mode=="family":
            rec=_candidate_record(args.input); cid=int(rec["_candidate_id"])
            cr=con.execute("SELECT curve_id FROM candidates WHERE id=?",(cid,)).fetchone()
            if cr is None or cr["curve_id"] is None:
                raise ValueError(f"candidate #{cid} is not attached to a stored exact rank-7-base curve")
            curve_id=int(cr["curve_id"]); parameter=rec.get("t")
            if parameter is None and rec.get("a") is not None and rec.get("b") is not None:
                parameter=str(QQ(rec["a"])/QQ(rec["b"]))
        else:
            curve_id=int(args.curve_id); parameter=None
        row=con.execute("SELECT id,parameter,a_invariants_json FROM curves WHERE id=?",(curve_id,)).fetchone()
        if row is None or not row["a_invariants_json"]:
            raise ValueError(f"curve #{curve_id} unavailable or lacks a-invariants")
        if parameter is None: parameter=row["parameter"]
        E=EllipticCurve(QQ,[QQ(str(v)) for v in json.loads(row["a_invariants_json"])])
        return curve_id,QQ(str(parameter)),E
    finally:
        con.close()

def _key(P):
    Q=-P
    return min((str(P[0]),str(P[1])),(str(Q[0]),str(Q[1])))

def _append(points,seen,P):
    if P.is_zero(): return False
    k=_key(P)
    if k in seen: return False
    seen.add(k); points.append(P); return True

def _search_model(E,timeout):
    if int(timeout)<=0: return E,(lambda P:E(P)),"stored",None
    try:
        p=run_global_minimal_model(E.a_invariants(),timeout=max(1,int(timeout)))
        Em=EllipticCurve(QQ,[QQ(str(v)) for v in p["a_invariants"]]); iso=Em.isomorphism_to(E)
        return Em,(lambda P:iso(P)),"minimal",float(p.get("runtime") or 0.0)
    except (ModelPrepFailure,ModelPrepTimeout,ArithmeticError,ValueError) as exc:
        return E,(lambda P:E(P)),"stored",repr(exc)

def build_result(args):
    curve_id,parameter,E=_subject(args)
    points=[]; seen=set(); gc=0; ge=None
    if args.include_generic:
        try:
            Ef=family.curve(parameter)
            if Ef is None:
                raise ArithmeticError("parameter is not on the exact rational rank-7 base locus")
            for P in map_points_exact(Ef,E,family.generic_section_points(parameter)):
                if _append(points,seen,P): gc+=1
        except Exception as exc:
            ge=repr(exc)
    rows=[]; extras=0; partial=False; model="skipped"; prep=None
    if int(args.max_points)>0:
        Es,to_stored,model,prep=_search_model(E,args.model_prep_timeout)
        ainvs=list(Es.a_invariants()); poly=completed_square_polynomial(ainvs)
        try: rp=probe_version(args.ratpoints)
        except (RatpointsNotFound,RatpointsTimeout) as exc:
            rp=None; partial=True; rows.append({"stage":None,"status":"ratpoints_unavailable","error":repr(exc)})
        if rp is not None:
            for h in args.stages:
                if extras>=int(args.max_points): break
                try: result=run_ratpoints(poly,int(h),executable=rp["executable"],timeout=max(1,int(args.timeout)))
                except RatpointsTimeout as exc:
                    partial=True; rows.append({"stage":int(h),"status":"timeout","error":repr(exc)}); continue
                except RatpointsFailure as exc:
                    partial=True; rows.append({"stage":int(h),"status":"error","error":repr(exc)}); continue
                added=0
                for raw in result["points"]:
                    if extras>=int(args.max_points): break
                    try:
                        xq=QQ(str(raw.x)); wq=QQ(str(raw.y))
                        yq=QQ(str(recover_weierstrass_y(ainvs,xq,wq)))
                        P=to_stored(Es(xq,yq)); P=E(P[0],P[1])
                    except Exception:
                        continue
                    if _append(points,seen,P): added+=1; extras+=1
                rows.append({"stage":int(h),"status":"completed","ratpoints_total":len(result["points"]),"new_exact":added})
    lift=None
    try:
        raw=family.rank7_base_lift(parameter)
        lift={"base_square_root":str(raw["z"]),"lifted_w2":str(raw["w2"])}
    except Exception:
        lift=None
    return {"schema":SCHEMA,"status":"partial" if partial else "completed","engine":"rational_diophantine_rank7_search","engine_version":ENGINE_VERSION,
            "algorithm":"genus1_rank7_basis_plus_completed_square_ratpoints","points":[[str(P[0]),str(P[1])] for P in points],"artifacts":[],
            "metadata":{"result_source":"typed_artifact","plugin_id":"rational_diophantine_rank7","mode":str(args.mode),"curve_id":int(curve_id),
                        "parameter":str(parameter),"rank7_base_lift":lift,"generic_sections_returned":gc,"generic_section_error":ge,
                        "ratpoints_extras_returned":extras,"search_model":model,"model_prep_detail":prep,"stages":rows,
                        "torsion_family":"C2 × C2","scientific_write_policy":"core_validated_artifacts_only"}}

def main(argv=None):
    args=parse_args(argv); result=build_result(args); path=os.environ.get(RESULT_ENV)
    if path: Path(path).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("RATIONAL_DIOPHANTINE_RANK7_RESULT="+json.dumps({"status":result["status"],"points":len(result["points"]),"curve_id":result["metadata"]["curve_id"]},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
