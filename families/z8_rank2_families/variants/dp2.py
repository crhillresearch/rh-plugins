"""Dujella–Peral II Z/8 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations
from sage.all import EllipticCurve, GF, QQ, ZZ
generic_rank=2
historical_generic_rank_lower=2
CONTROL_PARAMETER=QQ("19")
VARIANT_ID="dp2"

def name(): return "Z/8 rank-2 · Dujella–Peral II"
def _a_raw(u): return 500246412961-2069985157080*u+3162080774436*u**2-2895517882032*u**3+1873181389706*u**4-906769167048*u**5+333391978480*u**6-93284915496*u**7+19860033555*u**8-3216721224*u**9+396423280*u**10-37179432*u**11+2648426*u**12-141168*u**13+5316*u**14-120*u**15+u**16
def _b_raw(u): return 256*(u-6)**4*u**4*(6*u-29)**4*(841-522*u+137*u**2-18*u**3+u**4)**4
def a_coeff(u):
    u=QQ(u); return QQ(_a_raw(u))
def b_coeff(u):
    u=QQ(u); return QQ(_b_raw(u))
def _x_sections(u):
    u=QQ(u)
    return [16*(u-6)*u*(6*u-29)**3*(u**4-18*u**3+137*u**2-522*u+841)**2,((u-6)**2*u**2*(6*u-29)**2*(87-29*u+3*u**2)**2*(2523-1914*u+541*u**2-66*u**3+3*u**4)**2)/(4*(29-12*u+u**2)**2)]
def _sqrt_qq(value):
    value=QQ(value)
    if value<0: raise ArithmeticError("expected rational square, got negative value")
    n=ZZ(value.numerator()); d=ZZ(value.denominator())
    if not n.is_square() or not d.is_square(): raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt())/QQ(d.sqrt())
def curve(u):
    try:
        u=QQ(u); E=EllipticCurve(QQ,[0,a_coeff(u),0,b_coeff(u),0]); return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None
def curve_mod_p(r0,p0):
    try:
        p=int(p0)
        if p==2: return None
        K=GF(p); u=K(int(r0)); E=EllipticCurve(K,[0,_a_raw(u),0,_b_raw(u),0]); return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None
def generic_section_points(u):
    u=QQ(u); E=curve(u)
    if E is None: raise ArithmeticError(f"singular Dujella–Peral II specialization u={u}")
    A=a_coeff(u); B=b_coeff(u); out=[]
    for xx in _x_sections(u):
        x=QQ(xx); y=_sqrt_qq(x**3+A*x**2+B*x); out.append(E(x,y))
    if len(out)!=2 or any(P.is_zero() for P in out): raise ArithmeticError("Dujella–Peral II did not produce two nonzero sections")
    return out
def construction_check(u=CONTROL_PARAMETER):
    u=QQ(u); E=curve(u)
    if E is None: raise ArithmeticError(f"undefined Dujella–Peral II specialization u={u}")
    pts=generic_section_points(u); tors=E.torsion_subgroup().invariants()
    return {"variant":VARIANT_ID,"parameter":str(u),"sections":len(pts),"distinct_nonzero":len({(QQ(P[0]),QQ(P[1])) for P in pts}),"torsion_invariants":[int(x) for x in tors],"a_invariants":[str(a) for a in E.a_invariants()]}
def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate
    E=curve(CONTROL_PARAMETER)
    if E is None: raise RuntimeError("Dujella–Peral II control specialization is singular")
    pts=generic_section_points(CONTROL_PARAMETER)
    exact=run_exact_certificate(E.a_invariants(),[[P[0],P[1]] for P in pts],timeout=180)
    lower=int(exact.get("rank_lower_bound") or 0)
    return {"verified":bool(exact.get("independent") is True and lower>=2),"lower_bound":lower,"method":"two published full free generators + Rank Hunter exact independence certificate","certificate_version":"z8-rank2-dp2-generic-lower-v0.1.0","details":{"variant":VARIANT_ID,"control_parameter":str(CONTROL_PARAMETER),"section_count":len(pts),"specialization_certificate":exact,"paper_generic_rank":2}}
