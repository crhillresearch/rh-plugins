"""Shared Sage bridge for the six DMT-001 Triad Family variants."""
from __future__ import annotations
import importlib.util
from fractions import Fraction
from pathlib import Path

def _load_math():
    path=Path(__file__).with_name("triad_math.py")
    spec=importlib.util.spec_from_file_location("rank42_dmt_triad_math",path)
    if spec is None or spec.loader is None: raise ImportError(f"cannot load {path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

_math=_load_math()

def _sage():
    from sage.all import EllipticCurve, GF, QQ
    return QQ,GF,EllipticCurve

def _piezas_over(t):
    t2=t*t
    a=((t2-2*t-1)*(t2+2*t+3)*(3*t2-2*t+1))/(4*t*(t2-1)*(t2+2*t-1))
    b=(4*t*(t2-1)*(t2-2*t-1))/((t2+2*t-1)**3)
    c=(4*t*(t2-1)*(t2+2*t-1))/((t2-2*t-1)**3)
    d=((t2+2*t-1)*(t2-2*t+3)*(3*t2+2*t+1))/(4*t*(t2-1)*(t2-2*t-1))
    e=(-t*(t2+4*t+1)*(t2-4*t+1))/((t-1)*(t+1)*(t2+2*t-1)*(t2-2*t-1))
    f=((t-1)*(t+1)*(3*t2-1)*(t2-3))/(4*t*(t2+2*t-1)*(t2-2*t-1))
    return dict(zip(_math.LABELS,(a,b,c,d,e,f)))

def _curve_from_values(field,values,triple):
    u,v,w=(values[k] for k in triple); uv,uw,vw=u*v,u*w,v*w
    ainvs=[field(0),uv+uw+vw,field(0),uv*uw+uv*vw+uw*vw,uv*uw*vw]
    _,_,EllipticCurve=_sage(); E=EllipticCurve(field,ainvs)
    return None if E.discriminant()==0 else E

def curve(triple,t):
    QQ,_,_=_sage()
    try: tq=QQ(t); return _curve_from_values(QQ,_piezas_over(tq),triple)
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None

def curve_mod_p(triple,r,p):
    _,GF,_=_sage()
    try: F=GF(int(p)); tr=F(int(r)); return _curve_from_values(F,_piezas_over(tr),triple)
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None

def generic_section_points(triple,t):
    QQ,_,_=_sage(); tq=QQ(t); E=curve(triple,tq)
    if E is None: return []
    coords=_math.paper_section_coordinates(Fraction(str(tq)),triple)
    return [E(QQ(str(x)),QQ(str(y))) for x,y in coords]

def construction_check(triple,t="12/5"):
    E=curve(triple,t)
    if E is None: raise ArithmeticError(f"undefined DMT Triad specialization {triple} at t={t}")
    points=generic_section_points(triple,t)
    return {"triple":triple,"parameter":str(t),"sections":len(points),"distinct_nonzero":len({(str(P[0]),str(P[1])) for P in points if not P.is_zero()}),"a_invariants":[str(a) for a in E.a_invariants()]}

def validate_generic_rank_claim(triple):
    from rank42.exact_lb import run_exact_certificate
    control_parameter="12/5"; E=curve(triple,control_parameter)
    if E is None: raise RuntimeError(f"DMT Triad {triple} control t={control_parameter} is singular or undefined")
    points=generic_section_points(triple,control_parameter)
    if len(points)!=4: raise RuntimeError(f"DMT Triad {triple} did not produce four paper sections")
    exact=run_exact_certificate(E.a_invariants(),[[P[0],P[1]] for P in points],timeout=120)
    lower=int(exact.get("rank_lower_bound") or 0); verified=bool(exact.get("independent") is True and lower>=4)
    return {
        "verified":verified,"lower_bound":lower,
        "method":"DMT-001 explicit sections + exact specialized independence certificate",
        "certificate_version":"dmt-triad-rank4-v0.1.3",
        "details":{
            "triple":triple,"control_parameter":control_parameter,
            "section_labels":list(_math.PAPER_SECTIONS[triple]),"section_count":len(points),
            "specialization_certificate":exact,
            "generic_argument":"any Z-relation among the four explicit generic sections would specialize at this good fiber; exact independence after specialization therefore verifies their generic independence",
        },
    }
