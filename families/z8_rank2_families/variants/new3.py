"""Dujella–Kazalicki–Peral New III Z/8 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations
from sage.all import EllipticCurve, GF, QQ, ZZ
generic_rank=2
historical_generic_rank_lower=2
CONTROL_PARAMETER=QQ("10")
VARIANT_ID="new3"

def name(): return "Z/8 rank-2 · Dujella–Kazalicki–Peral New III"
def _a_raw(u): return -2*u**16+384*u**15-30128*u**14+1278592*u**13-32804472*u**12+545481088*u**11-6133914960*u**10+47788256896*u**9-261061974220*u**8+1003553394816*u**7-2705056497360*u**6+5051700355968*u**5-6379846519032*u**4+5221898865792*u**3-2583961693488*u**2+691617999744*u-75645718722
def _b_raw(u): return (u**2-56*u+147)**4*(u**2-8*u+3)**4*(u**4-32*u**3+278*u**2-672*u+441)**4
def a_coeff(u):
    u=QQ(u); return QQ(_a_raw(u))
def b_coeff(u):
    u=QQ(u); return QQ(_b_raw(u))
def _x_sections(u):
    u=QQ(u)
    return [(u**2-8*u+3)**2*(u**4-32*u**3+278*u**2-672*u+441)*(2*u**5-55*u**4+508*u**3-1834*u**2+3234*u-3087)**2,(u**2*(u**2-56*u+147)**2*(u**2-8*u+3)**4*(u**4-32*u**3+278*u**2-672*u+441)**3)/((u**5-22*u**4+262*u**3-1524*u**2+3465*u-2646)**2)]
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
    if E is None: raise ArithmeticError(f"singular Dujella–Kazalicki–Peral New III specialization u={u}")
    A=a_coeff(u); B=b_coeff(u); out=[]
    for xx in _x_sections(u):
        x=QQ(xx); y=_sqrt_qq(x**3+A*x**2+B*x); out.append(E(x,y))
    if len(out)!=2 or any(P.is_zero() for P in out): raise ArithmeticError("Dujella–Kazalicki–Peral New III did not produce two nonzero sections")
    return out
def construction_check(u=CONTROL_PARAMETER):
    u=QQ(u); E=curve(u)
    if E is None: raise ArithmeticError(f"undefined Dujella–Kazalicki–Peral New III specialization u={u}")
    pts=generic_section_points(u); tors=E.torsion_subgroup().invariants()
    return {"variant":VARIANT_ID,"parameter":str(u),"sections":len(pts),"distinct_nonzero":len({(QQ(P[0]),QQ(P[1])) for P in pts}),"torsion_invariants":[int(x) for x in tors],"a_invariants":[str(a) for a in E.a_invariants()]}
def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate
    E=curve(CONTROL_PARAMETER)
    if E is None: raise RuntimeError("Dujella–Kazalicki–Peral New III control specialization is singular")
    pts=generic_section_points(CONTROL_PARAMETER)
    exact=run_exact_certificate(E.a_invariants(),[[P[0],P[1]] for P in pts],timeout=180)
    lower=int(exact.get("rank_lower_bound") or 0)
    return {"verified":bool(exact.get("independent") is True and lower>=2),"lower_bound":lower,"method":"two published full free generators + Rank Hunter exact independence certificate","certificate_version":"z8-rank2-new3-generic-lower-v0.1.0","details":{"variant":VARIANT_ID,"control_parameter":str(CONTROL_PARAMETER),"section_count":len(pts),"specialization_certificate":exact,"paper_generic_rank":2}}
